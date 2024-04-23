import time
from typing import TYPE_CHECKING, Any, Dict, Optional, Type

from opentelemetry import context, metrics, propagate, trace
from opentelemetry.semconv.trace import SpanAttributes

if TYPE_CHECKING:
    from types import TracebackType

    from opentelemetry.context import Context
    from opentelemetry.metrics import Meter, MeterProvider
    from opentelemetry.trace import Span, Tracer, TracerProvider

    from faststream.broker.message import StreamMessage
    from faststream.types import AsyncFunc, AsyncFuncAny

from faststream import BaseMiddleware

_OTEL_SCHEMA = "https://opentelemetry.io/schemas/1.11.0"


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


def _create_span_name(destination: str, action: str) -> str:
    return f"{destination} {action}"


class MessageAction:
    CREATE = "create"
    PUBLISH = "publish"
    PROCESS = "process"
    RECEIVE = "receive"


class _MetricsContainer:
    __slots__ = (
        "active_requests_counter",
        "duration_histogram",
        "consumer_message_size_histogram",
        "publisher_message_size_histogram",
    )

    def __init__(self, meter: "Meter") -> None:
        self.active_requests_counter = meter.create_up_down_counter(
            name="faststream.consumer.active_requests",
            unit="requests",
            description="Measures the number of concurrent messages that are currently in-flight.",
        )
        self.duration_histogram = meter.create_histogram(
            name="faststream.consumer.duration",
            unit="s",
            description="Measures the duration of message processing.",
        )
        self.consumer_message_size_histogram = meter.create_histogram(
            name="faststream.consumer.message_size",
            unit="By",
            description="Measures the size of consumed messages.",
        )
        self.publisher_message_size_histogram = meter.create_histogram(
            name="faststream.publisher.message_size",
            unit="By",
            description="Measures the size of published messages.",
        )


class BaseTelemetryMiddleware(BaseMiddleware):
    def __init__(
        self,
        system: str,
        tracer: "Tracer",
        metrics_container: _MetricsContainer,
        msg: Optional[Any] = None,
    ) -> None:
        self.msg = msg
        self._system = system
        self._tracer = tracer
        self._metrics = metrics_container
        self._current_span: Optional[Span] = None
        self._origin_context: Optional[Context] = None

    async def publish_scope(
        self,
        call_next: "AsyncFunc",
        msg: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        headers = kwargs.pop("headers") or {}
        attributes = self._get_attrs_from_kwargs(kwargs)
        current_context = context.get_current()
        destination_name = kwargs.get("subject", "faststream")

        if self._current_span and self._current_span.is_recording():
            current_context = trace.set_span_in_context(
                self._current_span, current_context
            )
            propagate.inject(headers, context=self._origin_context)
        else:
            create_span = self._tracer.start_span(
                name=_create_span_name(destination_name, MessageAction.CREATE),
                kind=trace.SpanKind.CONSUMER,
                attributes=attributes,
            )
            current_context = trace.set_span_in_context(create_span)
            propagate.inject(headers, context=current_context)
            create_span.end()

        with self._tracer.start_as_current_span(
            name=_create_span_name(destination_name, MessageAction.PUBLISH),
            kind=trace.SpanKind.PRODUCER,
            attributes=attributes,
            context=current_context,
        ):
            result = await call_next(msg, *args, headers=headers, **kwargs)

        self._metrics.publisher_message_size_histogram.record(len(msg), attributes)
        return result

    async def consume_scope(
        self,
        call_next: "AsyncFuncAny",
        msg: "StreamMessage[Any]",
    ) -> Any:
        start_time = time.perf_counter()
        current_context = propagate.extract(msg.headers)
        destination_name = msg.raw_message.subject
        attributes = self._get_attrs_from_message(msg)

        if not len(current_context):
            create_span = self._tracer.start_span(
                name=_create_span_name(destination_name, MessageAction.CREATE),
                kind=trace.SpanKind.CONSUMER,
                attributes=attributes,
            )
            current_context = trace.set_span_in_context(create_span)
            create_span.end()

        self._origin_context = current_context
        self._metrics.active_requests_counter.add(1, attributes)
        self._metrics.publisher_message_size_histogram.record(len(msg.body), attributes)

        try:
            with self._tracer.start_as_current_span(
                name=_create_span_name(destination_name, MessageAction.PROCESS),
                kind=trace.SpanKind.CONSUMER,
                context=current_context,
                attributes=attributes,
                end_on_exit=False,
            ) as span:
                self._current_span = span
                new_context = trace.set_span_in_context(span, current_context)
                token = context.attach(new_context)
                result = await call_next(msg)
                context.detach(token)

            total_time = time.perf_counter() - start_time
            self._metrics.duration_histogram.record(
                amount=total_time, attributes=attributes
            )
        finally:
            self._metrics.active_requests_counter.add(-1, attributes)

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

    def _get_attrs_from_message(self, msg: "StreamMessage[Any]") -> Dict[str, Any]:
        return {
            SpanAttributes.MESSAGING_SYSTEM: self._system,
            SpanAttributes.MESSAGING_MESSAGE_ID: msg.correlation_id,
            SpanAttributes.MESSAGING_MESSAGE_CONVERSATION_ID: msg.correlation_id,
            SpanAttributes.MESSAGING_MESSAGE_PAYLOAD_SIZE_BYTES: len(msg.body),
            "messaging.destination_publish.name": msg.raw_message.subject,
        }

    def _get_attrs_from_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        attrs = {SpanAttributes.MESSAGING_SYSTEM: self._system}

        if (destination := kwargs.get("subject")) is not None:
            attrs[SpanAttributes.MESSAGING_DESTINATION_NAME] = destination
        if (message_id := kwargs.get("message_id")) is not None:
            attrs[SpanAttributes.MESSAGING_MESSAGE_ID] = message_id
        if (correlation_id := kwargs.get("correlation_id")) is not None:
            attrs[SpanAttributes.MESSAGING_MESSAGE_CONVERSATION_ID] = correlation_id

        return attrs


class TelemetryMiddleware:
    __slots__ = (
        "_tracer",
        "_meter",
        "_metrics",
    )

    def __init__(
        self,
        tracer_provider: Optional["TracerProvider"] = None,
        meter_provider: Optional["MeterProvider"] = None,
        meter: Optional["Meter"] = None,
    ) -> None:
        self._tracer = _get_tracer(tracer_provider)
        self._meter = _get_meter(meter_provider, meter)
        self._metrics = _MetricsContainer(self._meter)

    def __call__(self, msg: Optional[Any]) -> BaseMiddleware:
        return BaseTelemetryMiddleware(
            system="nats",
            tracer=self._tracer,
            metrics_container=self._metrics,
            msg=msg,
        )
