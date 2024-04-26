import asyncio
from typing import Any, ClassVar, Dict, Optional, Type, cast
from unittest.mock import Mock

import pytest
from dirty_equals import IsUUID
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import Span, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.semconv.trace import SpanAttributes as SpanAttr
from opentelemetry.trace import SpanKind

from faststream.broker.core.usecase import BrokerUsecase
from faststream.broker.middlewares.telemetry import (
    MessageAction as Action,
    TelemetryMiddleware,
)


@pytest.mark.asyncio()
class LocalTelemetryTestcase:
    messaging_system: str
    broker_class: Type[BrokerUsecase]
    timeout: int = 3
    subscriber_kwargs: ClassVar[Dict[str, Any]] = {}
    resource: Resource = Resource.create(attributes={"service.name": "faststream.test"})

    @pytest.fixture()
    def raw_broker(self):
        return None

    def patch_broker(
        self, raw_broker: BrokerUsecase, broker: BrokerUsecase
    ) -> BrokerUsecase:
        return broker

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
        destination: str,
        msg: str,
        parent_span_id: Optional[str] = None,
    ) -> None:
        attrs = span.attributes
        assert attrs[SpanAttr.MESSAGING_SYSTEM] == self.messaging_system
        assert attrs[SpanAttr.MESSAGING_MESSAGE_CONVERSATION_ID] == IsUUID
        assert span.name == f"{destination} {action}"
        assert span.kind in (SpanKind.CONSUMER, SpanKind.PRODUCER)

        if span.kind == SpanKind.PRODUCER and action in (Action.CREATE, Action.PUBLISH):
            assert attrs[SpanAttr.MESSAGING_DESTINATION_NAME] == destination

        if span.kind == SpanKind.CONSUMER and action in (Action.CREATE, Action.PROCESS):
            assert attrs["messaging.destination_publish.name"] == destination
            assert attrs[SpanAttr.MESSAGING_MESSAGE_ID] == IsUUID

        if action == Action.PROCESS:
            assert attrs[SpanAttr.MESSAGING_MESSAGE_PAYLOAD_SIZE_BYTES] == len(msg)

        if parent_span_id:
            assert span.parent.span_id == parent_span_id

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

        spans = trace_exporter.get_finished_spans()
        create, publish, process = cast("tuple[Span, Span, Span]", spans)
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

        spans = trace_exporter.get_finished_spans()
        create, pub1, pub2, proc1, proc2 = cast(
            "tuple[Span, Span, Span, Span, Span]", spans
        )
        parent_span_id = create.context.span_id

        self.assert_span(create, Action.CREATE, first_queue, msg)
        self.assert_span(pub1, Action.PUBLISH, first_queue, msg, parent_span_id)
        self.assert_span(proc1, Action.PROCESS, first_queue, msg, parent_span_id)
        self.assert_span(pub2, Action.PUBLISH, second_queue, msg, proc1.context.span_id)
        self.assert_span(proc2, Action.PROCESS, second_queue, msg, parent_span_id)

        assert (
            create.end_time
            < pub1.end_time
            < pub2.end_time
            < proc1.end_time
            < proc2.end_time
        )
        assert proc1.start_time < pub2.start_time < pub2.end_time < proc1.end_time

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

        create, process = cast("tuple[Span, Span]", trace_exporter.get_finished_spans())
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

        metrics = (
            metric_reader.get_metrics_data()
            .resource_metrics[0]
            .scope_metrics[0]
            .metrics
        )
        pub_mes_size, requests, cons_mes_size, duration = metrics

        assert pub_mes_size.data.data_points[0].count == 1
        assert pub_mes_size.data.data_points[0].sum == len(msg)

        assert requests.data.data_points[0].value == 0

        assert cons_mes_size.data.data_points[0].count == 1
        assert cons_mes_size.data.data_points[0].sum == len(msg)

        assert duration.data.data_points[0].count == 1

        assert event.is_set()
        mock.assert_called_once_with(msg)
