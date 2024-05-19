import asyncio
from typing import Optional
from unittest.mock import Mock

import pytest
from dirty_equals import IsStr, IsUUID
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace import Span, TracerProvider
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
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
    include_messages_counters = True
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

    async def test_batch(
        self,
        event: asyncio.Event,
        queue: str,
        mock: Mock,
        meter_provider: MeterProvider,
        metric_reader: InMemoryMetricReader,
        tracer_provider: TracerProvider,
        trace_exporter: InMemorySpanExporter,
    ):
        mid = self.telemetry_middleware_class(
            meter_provider=meter_provider, tracer_provider=tracer_provider
        )
        broker = self.broker_class(middlewares=(mid,))
        expected_msg_count = 3

        @broker.subscriber(queue, batch=True, **self.subscriber_kwargs)
        async def handler(m):
            mock(m)
            event.set()

        broker = self.patch_broker(broker)

        async with broker:
            await broker.start()
            tasks = (
                asyncio.create_task(broker.publish_batch(1, "hi", 3, topic=queue)),
                asyncio.create_task(event.wait()),
            )
            await asyncio.wait(tasks, timeout=self.timeout)

        metrics = self.get_metrics(metric_reader)
        spans = self.get_spans(trace_exporter)
        _, publish, process = spans

        assert (
            publish.attributes[SpanAttr.MESSAGING_BATCH_MESSAGE_COUNT]
            == expected_msg_count
        )
        assert (
            process.attributes[SpanAttr.MESSAGING_BATCH_MESSAGE_COUNT]
            == expected_msg_count
        )
        self.assert_metrics(metrics, count=expected_msg_count)

        assert event.is_set()
        mock.assert_called_once_with([1, "hi", 3])


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
