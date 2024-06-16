import asyncio
from unittest.mock import Mock

import pytest
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.semconv.trace import SpanAttributes as SpanAttr

from faststream.redis import ListSub, RedisBroker
from faststream.redis.opentelemetry import RedisTelemetryMiddleware
from tests.brokers.redis.test_consume import (
    TestConsume,
    TestConsumeList,
    TestConsumeStream,
)
from tests.brokers.redis.test_publish import TestPublish

from ..basic import LocalTelemetryTestcase


@pytest.mark.redis()
class TestTelemetry(LocalTelemetryTestcase):
    messaging_system = "redis"
    include_messages_counters = True
    broker_class = RedisBroker
    telemetry_middleware_class = RedisTelemetryMiddleware

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
        expected_link_count = 1

        @broker.subscriber(list=ListSub(queue, batch=True), **self.subscriber_kwargs)
        async def handler(m):
            mock(m)
            event.set()

        broker = self.patch_broker(broker)

        async with broker:
            await broker.start()
            tasks = (
                asyncio.create_task(broker.publish_batch(1, "hi", 3, list=queue)),
                asyncio.create_task(event.wait()),
            )
            await asyncio.wait(tasks, timeout=self.timeout)

        metrics = self.get_metrics(metric_reader)
        spans = self.get_spans(trace_exporter)
        _, publish, create_process, process = spans

        assert (
            publish.attributes[SpanAttr.MESSAGING_BATCH_MESSAGE_COUNT]
            == expected_msg_count
        )
        assert (
            process.attributes[SpanAttr.MESSAGING_BATCH_MESSAGE_COUNT]
            == expected_msg_count
        )
        assert len(create_process.links) == expected_link_count
        self.assert_metrics(metrics, count=expected_msg_count)

        assert event.is_set()
        mock.assert_called_once_with([1, "hi", 3])


@pytest.mark.redis()
class TestPublishWithTelemetry(TestPublish):
    def get_broker(self, apply_types: bool = False):
        return RedisBroker(
            middlewares=(RedisTelemetryMiddleware(),),
            apply_types=apply_types,
        )


@pytest.mark.redis()
class TestConsumeWithTelemetry(TestConsume):
    def get_broker(self, apply_types: bool = False):
        return RedisBroker(
            middlewares=(RedisTelemetryMiddleware(),),
            apply_types=apply_types,
        )


@pytest.mark.redis()
class TestConsumeListWithTelemetry(TestConsumeList):
    def get_broker(self, apply_types: bool = False):
        return RedisBroker(
            middlewares=(RedisTelemetryMiddleware(),),
            apply_types=apply_types,
        )


@pytest.mark.redis()
class TestConsumeStreamWithTelemetry(TestConsumeStream):
    def get_broker(self, apply_types: bool = False):
        return RedisBroker(
            middlewares=(RedisTelemetryMiddleware(),),
            apply_types=apply_types,
        )
