from typing import Optional

import pytest
from dirty_equals import IsStr, IsUUID
from opentelemetry.sdk.trace import Span
from opentelemetry.semconv.trace import SpanAttributes as SpanAttr
from opentelemetry.trace import SpanKind

from faststream.kafka import KafkaBroker
from faststream.kafka.opentelemetry import KafkaTelemetryMiddleware
from faststream.opentelemetry.consts import MESSAGING_DESTINATION_PUBLISH_NAME
from faststream.opentelemetry.middleware import MessageAction as Action
from tests.brokers.kafka.test_consume import TestConsume
from tests.brokers.kafka.test_publish import TestPublish

from ..basic import LocalTelemetryTestcase


@pytest.mark.kafka()
class TestTelemetry(LocalTelemetryTestcase):
    messaging_system = "kafka"
    broker_class = KafkaBroker
    telemetry_middleware_class = KafkaTelemetryMiddleware

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
            assert attrs[MESSAGING_DESTINATION_PUBLISH_NAME] == queue
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


@pytest.mark.kafka()
class TestPublishWithTelemetry(TestPublish):
    def get_broker(self, apply_types: bool = False):
        return KafkaBroker(
            middlewares=(KafkaTelemetryMiddleware(),),
            apply_types=apply_types,
        )


@pytest.mark.kafka()
class TestConsumeWithTelemetry(TestConsume):
    def get_broker(self, apply_types: bool = False):
        return KafkaBroker(
            middlewares=(KafkaTelemetryMiddleware(),),
            apply_types=apply_types,
        )
