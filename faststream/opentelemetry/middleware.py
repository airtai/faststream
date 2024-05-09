import time
from typing import TYPE_CHECKING, Any, Callable, Optional, Sequence, Type

from opentelemetry import context, metrics, propagate, trace
from opentelemetry.semconv.trace import SpanAttributes

from faststream import BaseMiddleware
from faststream.opentelemetry.consts import MessageAction
from faststream.opentelemetry.provider import TelemetrySettingsProvider

if TYPE_CHECKING:
    from types import TracebackType

    from opentelemetry.context import Context
    from opentelemetry.metrics import Meter, MeterProvider
    from opentelemetry.trace import Span, Tracer, TracerProvider

    from faststream.broker.message import StreamMessage
    from faststream.types import AsyncFunc, AsyncFuncAny


_OTEL_SCHEMA = "https://opentelemetry.io/schemas/1.11.0"


def _create_span_name(destination: str, action: str) -> str:
    return f"{destination} {action}"


class _MetricsContainer:
    __slots__ = (
        "publish_duration",
        "publish_counter",
        "process_duration",
        "process_counter",
    )

    def __init__(self, meter: "Meter") -> None:
        # Metric attributes: messaging.system, error.type, messaging.destination.name/messaging.destination_publish.name
        self.publish_duration = meter.create_histogram(
            name="messaging.publish.duration",
            unit="s",
            description="Measures the duration of publish operation.",
        )
        self.publish_counter = meter.create_counter(
            name="messaging.publish.messages",
            unit="message",
            description="Measures the number of published messages.",
        )
        self.process_duration = meter.create_histogram(
            name="messaging.process.duration",
            unit="s",
            description="Measures the duration of process operation.",
        )
        self.process_counter = meter.create_counter(
            name="messaging.process.messages",
            unit="message",
            description="Measures the number of processed messages.",
        )


class BaseTelemetryMiddleware(BaseMiddleware):
    def __init__(
        self,
        *,
        tracer: "Tracer",
        settings_provider_factory: Callable[[Any], TelemetrySettingsProvider[Any]],
        metrics_container: _MetricsContainer,
        msg: Optional[Any] = None,
    ) -> None:
        self.msg = msg

        self._tracer = tracer
        self._metrics = metrics_container
        self._current_span: Optional[Span] = None
        self._origin_context: Optional[Context] = None
        self.__settings_provider = settings_provider_factory(msg)

    async def publish_scope(
        self,
        call_next: "AsyncFunc",
        msg: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        provider = self.__settings_provider

        attributes = provider.get_publish_attrs_from_kwargs(kwargs)

        current_context = context.get_current()
        destination_name = provider.get_publish_destination_name(kwargs)

        headers = kwargs.pop("headers", {}) or {}
        if self._current_span and self._current_span.is_recording():
            current_context = trace.set_span_in_context(
                self._current_span, current_context
            )
            propagate.inject(headers, context=self._origin_context)

        else:
            create_span = self._tracer.start_span(
                name=_create_span_name(destination_name, MessageAction.CREATE),
                kind=trace.SpanKind.PRODUCER,
                attributes=attributes,
            )
            current_context = trace.set_span_in_context(create_span)
            propagate.inject(headers, context=current_context)
            create_span.end()

        start_time = time.perf_counter()

        try:
            with self._tracer.start_as_current_span(
                name=_create_span_name(destination_name, MessageAction.PUBLISH),
                kind=trace.SpanKind.PRODUCER,
                attributes=attributes,
                context=current_context,
            ) as span:
                span.set_attribute(
                    SpanAttributes.MESSAGING_OPERATION, MessageAction.PUBLISH
                )
                result = await call_next(msg, *args, headers=headers, **kwargs)

        except Exception as e:
            attributes["error.type"] = type(e).__name__
            raise

        finally:
            self._metrics.publish_duration.record(
                amount=time.perf_counter() - start_time,
                attributes=attributes,
            )
            self._metrics.publish_counter.add(
                amount=len(msg) if isinstance(msg, Sequence) else 1,
                attributes=attributes
            )

        return result

    async def consume_scope(
        self,
        call_next: "AsyncFuncAny",
        msg: "StreamMessage[Any]",
    ) -> Any:
        provider = self.__settings_provider

        current_context = propagate.extract(msg.headers)
        destination_name = provider.get_consume_destination_name(msg)
        attributes = provider.get_consume_attrs_from_message(msg)

        if not len(current_context):
            create_span = self._tracer.start_span(
                name=_create_span_name(destination_name, MessageAction.CREATE),
                kind=trace.SpanKind.CONSUMER,
                attributes=attributes,
            )
            current_context = trace.set_span_in_context(create_span)
            create_span.end()

        self._origin_context = current_context
        start_time = time.perf_counter()

        try:
            with self._tracer.start_as_current_span(
                name=_create_span_name(destination_name, MessageAction.PROCESS),
                kind=trace.SpanKind.CONSUMER,
                context=current_context,
                attributes=attributes,
                end_on_exit=False,
            ) as span:
                span.set_attribute(
                    SpanAttributes.MESSAGING_OPERATION, MessageAction.PROCESS
                )
                self._current_span = span
                new_context = trace.set_span_in_context(span, current_context)
                token = context.attach(new_context)
                result = await call_next(msg)
                context.detach(token)

        except Exception as e:
            attributes["error.type"] = type(e).__name__
            raise

        finally:
            self._metrics.process_duration.record(
                amount=time.perf_counter() - start_time,
                attributes=attributes,
            )
            self._metrics.process_counter.add(
                amount=len(msg) if isinstance(msg, Sequence) else 1,
                attributes=attributes
            )

        return result

    async def after_processed(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exc_tb: Optional["TracebackType"] = None,
    ) -> Optional[bool]:
        if self._current_span and self._current_span.is_recording():
            self._current_span.end()
        return False


class TelemetryMiddleware:
    # NOTE: should it be class or function?
    __slots__ = (
        "_tracer",
        "_meter",
        "_metrics",
        "_settings_provider_factory",
    )

    def __init__(
        self,
        *,
        settings_provider_factory: Callable[[Any], TelemetrySettingsProvider[Any]],
        tracer_provider: Optional["TracerProvider"] = None,
        meter_provider: Optional["MeterProvider"] = None,
        meter: Optional["Meter"] = None,
    ) -> None:
        self._tracer = _get_tracer(tracer_provider)
        self._meter = _get_meter(meter_provider, meter)
        self._metrics = _MetricsContainer(self._meter)
        self._settings_provider_factory = settings_provider_factory

    def __call__(self, msg: Optional[Any]) -> BaseMiddleware:
        return BaseTelemetryMiddleware(
            tracer=self._tracer,
            metrics_container=self._metrics,
            settings_provider_factory=self._settings_provider_factory,
            msg=msg,
        )


def _get_meter(
    meter_provider: Optional["MeterProvider"] = None,
    meter: Optional["Meter"] = None,
) -> "Meter":
    if meter is None:
        return metrics.get_meter(
            __name__,
            meter_provider=meter_provider,
            schema_url=_OTEL_SCHEMA,
        )
    return meter


def _get_tracer(tracer_provider: Optional["TracerProvider"] = None) -> "Tracer":
    return trace.get_tracer(
        __name__,
        tracer_provider=tracer_provider,
        schema_url=_OTEL_SCHEMA,
    )
