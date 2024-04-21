import time
from typing import Any, Dict, Optional

from opentelemetry import context, metrics, propagate, trace
from opentelemetry.metrics import Meter, MeterProvider
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.trace import Span, Tracer, TracerProvider

from faststream import BaseMiddleware
from faststream.broker.message import StreamMessage
from faststream.types import AsyncFunc, AsyncFuncAny

_OTEL_SCHEMA = "https://opentelemetry.io/schemas/1.11.0"


def _build_meter(
    meter_provider: Optional[MeterProvider] = None,
    meter: Optional[Meter] = None,
) -> Meter:
    if meter is None:
        return metrics.get_meter(
            __name__,
            meter_provider=meter_provider,
            schema_url=_OTEL_SCHEMA,
        )
    return meter


def _build_tracer(tracer_provider: Optional[TracerProvider] = None) -> Tracer:
    return trace.get_tracer(
        __name__,
        tracer_provider=tracer_provider,
        schema_url=_OTEL_SCHEMA,
    )


class _MetricsContainer:
    __slots__ = (
        "active_requests_counter",
        "duration_histogram",
        "consumer_message_size_histogram",
        "publisher_message_size_histogram",
    )

    def __init__(self, meter: Meter) -> None:
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


class _TelemetryMiddleware(BaseMiddleware):
    def __init__(
        self,
        msg: StreamMessage[Any],
        tracer: Tracer,
        metrics_container: _MetricsContainer,
    ) -> None:
        self.msg = msg
        self._system = "nats"
        self._tracer = tracer
        self._metrics = metrics_container
        self._current_span: Optional[Span] = None

    async def publish_scope(
        self,
        call_next: "AsyncFunc",
        msg: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        headers = kwargs.pop("headers") or {}
        span_name = f"{kwargs.get('subject')} publish"
        attributes = self._get_attrs_from_kwargs(kwargs)
        current_context = trace.set_span_in_context(self._current_span) if self._current_span else None

        with self._tracer.start_as_current_span(
            name=span_name,
            kind=trace.SpanKind.PRODUCER,
            attributes=attributes,
            context=current_context,
        ) as span:
            propagate.inject(headers, context=trace.set_span_in_context(span))
            result = await super().publish_scope(
                call_next,
                msg,
                headers=headers,
                **kwargs,
            )

        self._metrics.publisher_message_size_histogram.record(len(msg), attributes)
        return result

    async def consume_scope(
        self,
        call_next: AsyncFuncAny,
        msg: StreamMessage[Any],
    ) -> Any:
        start_time = time.perf_counter()
        span_context = propagate.extract(msg.headers)
        span_name = f"{msg.raw_message.subject} receive"
        attributes = self._get_attrs_from_message(msg)

        self._metrics.active_requests_counter.add(1, attributes)
        self._metrics.publisher_message_size_histogram.record(len(msg.body), attributes)

        try:
            with self._tracer.start_as_current_span(
                name=span_name,
                kind=trace.SpanKind.CONSUMER,
                context=span_context,
                attributes=attributes,
            ) as span:
                self._current_span = span
                new_context = trace.set_span_in_context(span, span_context)
                token = context.attach(new_context)
                result = await call_next(msg)
                context.detach(token)

            total_time = time.perf_counter() - start_time
            self._metrics.duration_histogram.record(amount=total_time, attributes=attributes)
        finally:
            self._metrics.active_requests_counter.add(-1, attributes)

        return result

    def _get_attrs_from_message(self, msg: StreamMessage[Any]) -> Dict[str, Any]:
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
    __slots__ = ("_tracer", "_meter", "_metrics")

    def __init__(
            self,
            tracer_provider: Optional[TracerProvider] = None,
            meter_provider: Optional[MeterProvider] = None,
            meter: Optional[Meter] = None,
    ) -> None:
        self._tracer = _build_tracer(tracer_provider)
        self._meter = _build_meter(meter_provider, meter)
        self._metrics = _MetricsContainer(self._meter)

    def __call__(self, msg: StreamMessage[Any]) -> _TelemetryMiddleware:
        return _TelemetryMiddleware(
            msg=msg,
            tracer=self._tracer,
            metrics_container=self._metrics,
        )
