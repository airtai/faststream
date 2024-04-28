import asyncio
from typing import Any, ClassVar, Dict, List, Optional, Tuple, Type, cast
from unittest.mock import Mock

import pytest
from dirty_equals import IsUUID
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics._internal.point import Metric
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import Span, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.semconv.trace import SpanAttributes as SpanAttr
from opentelemetry.trace import SpanKind

from faststream.broker.core.usecase import BrokerUsecase
from faststream.opentelemetry.middleware import MessageAction as Action
from faststream.opentelemetry.middleware import TelemetryMiddleware


@pytest.mark.asyncio()
class LocalTelemetryTestcase:
    messaging_system: str
    broker_class: Type[BrokerUsecase]
    timeout: int = 3
    subscriber_kwargs: ClassVar[Dict[str, Any]] = {}
    resource: Resource = Resource.create(attributes={"service.name": "faststream.test"})

    def patch_broker(
        self, raw_broker: BrokerUsecase, broker: BrokerUsecase
    ) -> BrokerUsecase:
        return broker

    def destination_name(self, queue: str) -> str:
        return queue

    @staticmethod
    def get_spans(exporter: InMemorySpanExporter) -> List[Span]:
        spans = cast(Tuple[Span, ...], exporter.get_finished_spans())
        return sorted(spans, key=lambda s: s.start_time)

    @staticmethod
    def get_metrics(
        reader: InMemoryMetricReader,
    ) -> Tuple[Metric, Metric, Metric, Metric]:
        """Get sorted metrics.

        Return order:
            - faststream.consumer.active_requests
            - faststream.consumer.duration
            - faststream.consumer.message_size
            - faststream.publisher.message_size
        """
        metrics = reader.get_metrics_data()
        metrics = metrics.resource_metrics[0].scope_metrics[0].metrics
        metrics = sorted(metrics, key=lambda m: m.name)
        requests, cons_mes_size, duration, pub_mes_size = metrics
        return requests, duration, cons_mes_size, pub_mes_size

    @pytest.fixture()
    def raw_broker(self):
        return None

    @pytest.fixture()
    def tracer_provider(self) -> TracerProvider:
        tracer_provider = TracerProvider(resource=self.resource)
        return tracer_provider

    @pytest.fixture()
    def trace_exporter(self, tracer_provider: TracerProvider) -> InMemorySpanExporter:
        exporter = InMemorySpanExporter()
        tracer_provider.add_span_processor(SimpleSpanProcessor(exporter))
        return exporter

    @pytest.fixture()
    def metric_reader(self) -> InMemoryMetricReader:
        return InMemoryMetricReader()

    @pytest.fixture()
    def meter_provider(self, metric_reader: InMemoryMetricReader) -> MeterProvider:
        return MeterProvider(metric_readers=(metric_reader,), resource=self.resource)

    def assert_span(
        self,
        span: Span,
        action: str,
        queue: str,
        msg: str,
        parent_span_id: Optional[str] = None,
    ) -> None:
        attrs = span.attributes
        assert attrs[SpanAttr.MESSAGING_SYSTEM] == self.messaging_system, attrs[
            SpanAttr.MESSAGING_SYSTEM
        ]
        assert attrs[SpanAttr.MESSAGING_MESSAGE_CONVERSATION_ID] == IsUUID, attrs[
            SpanAttr.MESSAGING_MESSAGE_CONVERSATION_ID
        ]
        assert span.name == f"{self.destination_name(queue)} {action}", span.name
        assert span.kind in (SpanKind.CONSUMER, SpanKind.PRODUCER), span.kind

        if span.kind == SpanKind.PRODUCER and action in (Action.CREATE, Action.PUBLISH):
            assert attrs[SpanAttr.MESSAGING_DESTINATION_NAME] == queue, attrs[
                SpanAttr.MESSAGING_DESTINATION_NAME
            ]

        if span.kind == SpanKind.CONSUMER and action in (Action.CREATE, Action.PROCESS):
            assert attrs["messaging.destination_publish.name"] == queue, attrs[
                "messaging.destination_publish.name"
            ]
            assert attrs[SpanAttr.MESSAGING_MESSAGE_ID] == IsUUID, attrs[
                SpanAttr.MESSAGING_MESSAGE_ID
            ]

        if action == Action.PROCESS:
            assert attrs[SpanAttr.MESSAGING_MESSAGE_PAYLOAD_SIZE_BYTES] == len(
                msg
            ), attrs[SpanAttr.MESSAGING_MESSAGE_PAYLOAD_SIZE_BYTES]
            assert attrs[SpanAttr.MESSAGING_OPERATION] == action, attrs[
                SpanAttr.MESSAGING_OPERATION
            ]

        if action == Action.PUBLISH:
            assert attrs[SpanAttr.MESSAGING_OPERATION] == action, attrs[
                SpanAttr.MESSAGING_OPERATION
            ]

        if parent_span_id:
            assert span.parent.span_id == parent_span_id, span.parent.span_id

    async def test_subscriber_create_publish_process_span(
        self,
        event: asyncio.Event,
        queue: str,
        mock: Mock,
        tracer_provider: TracerProvider,
        trace_exporter: InMemorySpanExporter,
        raw_broker,
    ):
        mid = TelemetryMiddleware(tracer_provider=tracer_provider)
        broker = self.broker_class(middlewares=(mid,))

        @broker.subscriber(queue, **self.subscriber_kwargs)
        async def handler(m):
            mock(m)
            event.set()

        broker = self.patch_broker(raw_broker, broker)
        msg = "start"

        async with broker:
            await broker.start()
            tasks = (
                asyncio.create_task(broker.publish(msg, queue)),
                asyncio.create_task(event.wait()),
            )
            await asyncio.wait(tasks, timeout=self.timeout)

        create, publish, process = self.get_spans(trace_exporter)
        parent_span_id = create.context.span_id

        self.assert_span(create, Action.CREATE, queue, msg)
        self.assert_span(publish, Action.PUBLISH, queue, msg, parent_span_id)
        self.assert_span(process, Action.PROCESS, queue, msg, parent_span_id)

        assert event.is_set()
        mock.assert_called_once_with(msg)

    async def test_chain_subscriber_publisher(
        self,
        event: asyncio.Event,
        queue: str,
        mock: Mock,
        tracer_provider: TracerProvider,
        trace_exporter: InMemorySpanExporter,
        raw_broker,
    ):
        mid = TelemetryMiddleware(tracer_provider=tracer_provider)
        broker = self.broker_class(middlewares=(mid,))

        first_queue = queue
        second_queue = queue + "2"

        @broker.subscriber(first_queue, **self.subscriber_kwargs)
        @broker.publisher(second_queue)
        async def handler1(m):
            return m

        @broker.subscriber(second_queue, **self.subscriber_kwargs)
        async def handler2(m):
            mock(m)
            event.set()

        broker = self.patch_broker(raw_broker, broker)
        msg = "start"

        async with broker:
            await broker.start()
            tasks = (
                asyncio.create_task(broker.publish(msg, queue)),
                asyncio.create_task(event.wait()),
            )
            await asyncio.wait(tasks, timeout=self.timeout)

        spans = self.get_spans(trace_exporter)
        create, pub1, proc1, pub2, proc2 = spans
        parent_span_id = create.context.span_id

        self.assert_span(create, Action.CREATE, first_queue, msg)
        self.assert_span(pub1, Action.PUBLISH, first_queue, msg, parent_span_id)
        self.assert_span(proc1, Action.PROCESS, first_queue, msg, parent_span_id)
        self.assert_span(pub2, Action.PUBLISH, second_queue, msg, proc1.context.span_id)
        self.assert_span(proc2, Action.PROCESS, second_queue, msg, parent_span_id)

        assert (
            create.start_time
            < pub1.start_time
            < proc1.start_time
            < pub2.start_time
            < proc2.start_time
        )

        assert event.is_set()
        mock.assert_called_once_with(msg)

    async def test_no_trace_context_create_process_span(
        self,
        event: asyncio.Event,
        queue: str,
        mock: Mock,
        tracer_provider: TracerProvider,
        trace_exporter: InMemorySpanExporter,
        raw_broker,
    ):
        mid = TelemetryMiddleware(tracer_provider=tracer_provider)
        broker = self.broker_class(middlewares=(mid,))

        @broker.subscriber(queue, **self.subscriber_kwargs)
        async def handler(m):
            mock(m)
            event.set()

        broker = self.patch_broker(raw_broker, broker)
        msg = "start"

        async with broker:
            await broker.start()
            broker._middlewares = ()
            tasks = (
                asyncio.create_task(broker.publish(msg, queue)),
                asyncio.create_task(event.wait()),
            )
            await asyncio.wait(tasks, timeout=self.timeout)

        create, process = self.get_spans(trace_exporter)
        parent_span_id = create.context.span_id

        self.assert_span(create, Action.CREATE, queue, msg)
        self.assert_span(process, Action.PROCESS, queue, msg, parent_span_id)

        assert event.is_set()
        mock.assert_called_once_with(msg)

    async def test_subscriber_metrics(
        self,
        event: asyncio.Event,
        queue: str,
        mock: Mock,
        meter_provider: MeterProvider,
        metric_reader: InMemoryMetricReader,
        raw_broker,
    ):
        expected_requests_in_flight = 0
        expected_publishing_count = 1
        expected_consuming_count = 1

        mid = TelemetryMiddleware(meter_provider=meter_provider)
        broker = self.broker_class(middlewares=(mid,))

        @broker.subscriber(queue, **self.subscriber_kwargs)
        async def handler(m):
            mock(m)
            event.set()

        broker = self.patch_broker(raw_broker, broker)
        msg = "start"

        async with broker:
            await broker.start()
            tasks = (
                asyncio.create_task(broker.publish(msg, queue)),
                asyncio.create_task(event.wait()),
            )
            await asyncio.wait(tasks, timeout=self.timeout)

        metrics = self.get_metrics(metric_reader)
        requests, cons_mes_size, duration, pub_mes_size = metrics

        assert requests.data.data_points[0].value == expected_requests_in_flight

        assert cons_mes_size.data.data_points[0].count == expected_consuming_count
        assert cons_mes_size.data.data_points[0].sum == len(msg)

        assert duration.data.data_points[0].count == expected_consuming_count

        assert pub_mes_size.data.data_points[0].count == expected_publishing_count
        assert pub_mes_size.data.data_points[0].sum == len(msg)

        assert event.is_set()
        mock.assert_called_once_with(msg)
