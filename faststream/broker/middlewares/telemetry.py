from timeit import default_timer
from typing import Any, Dict, List, Optional

from opentelemetry import metrics, propagate, trace
from opentelemetry.metrics import Meter, MeterProvider
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.trace import TracerProvider
from typing_extensions import Self

from faststream import BaseMiddleware, context
from faststream.broker.message import StreamMessage
from faststream.types import AsyncFunc, AsyncFuncAny

_OPEN_TELEMETRY_SCHEMA = "https://opentelemetry.io/schemas/1.11.0"

_MESSAGE_ATTRIBUTE_MAPPING = {
    SpanAttributes.MESSAGING_MESSAGE_ID: "message_id",
    SpanAttributes.MESSAGING_MESSAGE_CONVERSATION_ID: "correlation_id",
}


def _get_attributes_from_message(
    msg: StreamMessage[Any],
    attr_keys: Optional[List[str]] = None,
    default_attrs: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    attributes = default_attrs.copy() if default_attrs else {}
    attr_keys = attr_keys if attr_keys else list(_MESSAGE_ATTRIBUTE_MAPPING.keys())

    for k in attr_keys:
        value = getattr(msg, _MESSAGE_ATTRIBUTE_MAPPING[k], None)
        if value is None:
            continue
        attributes[k] = value

    return attributes


def _get_attributes_from_kwargs(
    kwargs: Dict[str, Any],
    attr_keys: Optional[List[str]] = None,
    default_attrs: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    attributes = default_attrs.copy() if default_attrs else {}
    attr_keys = attr_keys if attr_keys else list(_MESSAGE_ATTRIBUTE_MAPPING.keys())

    for k in attr_keys:
        value = kwargs.get(_MESSAGE_ATTRIBUTE_MAPPING[k], None)
        if value is None:
            continue
        attributes[k] = value

    return attributes


class TelemetryMiddleware(BaseMiddleware):
    def __init__(
        self,
        tracer_provider: Optional[TracerProvider] = None,
        meter_provider: Optional[MeterProvider] = None,
        meter: Optional[Meter] = None,
    ) -> None:
        self.tracer = trace.get_tracer(
            __name__,
            tracer_provider=tracer_provider,
            schema_url=_OPEN_TELEMETRY_SCHEMA,
        )
        self.meter = (
            metrics.get_meter(
                __name__,
                meter_provider=meter_provider,
                schema_url=_OPEN_TELEMETRY_SCHEMA,
            )
            if meter is None
            else meter
        )

        self.active_requests_counter = self.meter.create_up_down_counter(
            name="faststream.active_requests",
            unit="requests",
            description="measures the number of concurrent messages that are currently in-flight",
        )
        self.duration_histogram = self.meter.create_histogram(
            name="faststream.consume.duration",
            unit="ms",
            description="measures the duration of message consumption",
        )
        self.default_attributes: Dict[str, Any] = {
            SpanAttributes.MESSAGING_SYSTEM: "nats"
        }

    async def consume_scope(
        self,
        call_next: AsyncFuncAny,
        msg: StreamMessage[Any],
    ) -> Any:
        start_time = default_timer()

        span_context = propagate.extract(msg.headers)
        span_name = f"{context.get('handler_').call_name} consume"

        attributes = _get_attributes_from_message(
            msg, default_attrs=self.default_attributes
        )
        attributes[SpanAttributes.MESSAGING_MESSAGE_PAYLOAD_SIZE_BYTES] = len(msg.body)

        self.active_requests_counter.add(1, attributes)

        try:
            with self.tracer.start_as_current_span(
                name=span_name,
                kind=trace.SpanKind.CONSUMER,
                context=span_context,
                attributes=attributes,
            ) as span:
                context.set_local("span", span)
                result = await call_next(msg)
        finally:
            self.active_requests_counter.add(-1, attributes)
            self.duration_histogram.record(
                amount=round((default_timer() - start_time) * 1000, 1),
                attributes=attributes,
            )

        return result

    async def publish_scope(
        self,
        call_next: "AsyncFunc",
        msg: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        headers = kwargs.pop("headers") or {}
        attributes = _get_attributes_from_kwargs(
            kwargs, default_attrs=self.default_attributes
        )

        with self.tracer.start_as_current_span(
            name="publish",
            kind=trace.SpanKind.PRODUCER,
            attributes=attributes,
        ) as span:
            context.set_local("span", span)
            propagate.inject(headers)
            result = await super().publish_scope(
                call_next,
                msg,
                headers=headers,
                **kwargs,
            )

        return result

    def __call__(self, msg: Optional[Any]) -> Self:
        self.msg = msg
        return self
