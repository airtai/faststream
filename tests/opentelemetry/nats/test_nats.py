import asyncio
from unittest.mock import Mock

import pytest
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.semconv.trace import SpanAttributes as SpanAttr

from faststream.nats import JStream, NatsBroker, PullSub
from faststream.nats.opentelemetry import NatsTelemetryMiddleware
from tests.brokers.nats.test_consume import TestConsume
from tests.brokers.nats.test_publish import TestPublish

from ..basic import LocalTelemetryTestcase


@pytest.fixture()
def stream(queue):
    return JStream(queue)


@pytest.mark.nats()
class TestTelemetry(LocalTelemetryTestcase):
    messaging_system = "nats"
    include_messages_counters = True
    broker_class = NatsBroker
    telemetry_middleware_class = NatsTelemetryMiddleware

    async def test_batch(
        self,
        event: asyncio.Event,
        queue: str,
        mock: Mock,
        stream: JStream,
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

        @broker.subscriber(
            queue,
            stream=stream,
            pull_sub=PullSub(3, batch=True),
            **self.subscriber_kwargs,
        )
        async def handler(m):
            mock(m)
            event.set()

        broker = self.patch_broker(broker)

        async with broker:
            await broker.start()
            tasks = (
                asyncio.create_task(broker.publish(1, queue)),
                asyncio.create_task(broker.publish("hi", queue)),
                asyncio.create_task(broker.publish(3, queue)),
                asyncio.create_task(event.wait()),
            )
            await asyncio.wait(tasks, timeout=self.timeout)

        metrics = self.get_metrics(metric_reader)
        proc_dur, proc_msg, pub_dur, pub_msg = metrics
        spans = self.get_spans(trace_exporter)
        process = spans[-1]

        assert (
            process.attributes[SpanAttr.MESSAGING_BATCH_MESSAGE_COUNT]
            == expected_msg_count
        )
        assert proc_msg.data.data_points[0].value == expected_msg_count
        assert pub_msg.data.data_points[0].value == expected_msg_count
        assert proc_dur.data.data_points[0].count == 1
        assert pub_dur.data.data_points[0].count == expected_msg_count

        assert event.is_set()
        mock.assert_called_once_with([1, "hi", 3])


@pytest.mark.nats()
class TestPublishWithTelemetry(TestPublish):
    def get_broker(self, apply_types: bool = False):
        return NatsBroker(
            middlewares=(NatsTelemetryMiddleware(),),
            apply_types=apply_types,
        )


@pytest.mark.nats()
class TestConsumeWithTelemetry(TestConsume):
    def get_broker(self, apply_types: bool = False):
        return NatsBroker(
            middlewares=(NatsTelemetryMiddleware(),),
            apply_types=apply_types,
        )
