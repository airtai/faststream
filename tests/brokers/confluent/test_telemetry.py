from typing import Any, ClassVar, Dict, Optional

import pytest
from dirty_equals import IsStr, IsUUID
from opentelemetry.sdk.trace import Span
from opentelemetry.semconv.trace import SpanAttributes as SpanAttr
from opentelemetry.trace import SpanKind

from faststream.broker.middlewares.telemetry import MessageAction as Action
from faststream.confluent import KafkaBroker
from tests.brokers.base.telemetry import LocalTelemetryTestcase


@pytest.mark.confluent()
class TestTelemetry(LocalTelemetryTestcase):
    messaging_system = "kafka"
    timeout: int = 10
    subscriber_kwargs: ClassVar[Dict[str, Any]] = {"auto_offset_reset": "earliest"}
    broker_class = KafkaBroker

    def assert_span(
        self,
        span: Span,
        action: str,
        queue: str,
        msg: str,
        parent_span_id: Optional[str] = None,
    ) -> None:
        attrs = span.attributes
        assert attrs[SpanAttr.MESSAGING_SYSTEM] == self.messaging_system
        assert attrs[SpanAttr.MESSAGING_MESSAGE_CONVERSATION_ID] == IsUUID
        assert span.name == f"{self.destination_name(queue)} {action}"
        assert span.kind in (SpanKind.CONSUMER, SpanKind.PRODUCER)

        if span.kind == SpanKind.PRODUCER and action in (Action.CREATE, Action.PUBLISH):
            assert attrs[SpanAttr.MESSAGING_DESTINATION_NAME] == queue

        if span.kind == SpanKind.CONSUMER and action in (Action.CREATE, Action.PROCESS):
            assert attrs["messaging.destination_publish.name"] == queue
            assert attrs[SpanAttr.MESSAGING_MESSAGE_ID] == IsStr(regex=r"0-.+")
            assert attrs[SpanAttr.MESSAGING_KAFKA_DESTINATION_PARTITION] == 0
            assert attrs[SpanAttr.MESSAGING_KAFKA_MESSAGE_OFFSET] == 0

        if action == Action.PROCESS:
            assert attrs[SpanAttr.MESSAGING_MESSAGE_PAYLOAD_SIZE_BYTES] == len(msg)
            assert attrs[SpanAttr.MESSAGING_OPERATION] == action

        if action == Action.PUBLISH:
            assert attrs[SpanAttr.MESSAGING_OPERATION] == action

        if parent_span_id:
            assert span.parent.span_id == parent_span_id
