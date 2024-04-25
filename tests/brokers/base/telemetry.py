import asyncio
from typing import Any, ClassVar, Dict, Optional, Type, cast
from unittest.mock import Mock

import pytest
from dirty_equals import IsUUID
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import Span, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.trace import SpanKind

from faststream.broker.core.usecase import BrokerUsecase
from faststream.broker.middlewares.telemetry import MessageAction, TelemetryMiddleware


@pytest.mark.asyncio()
class LocalTelemetryTestcase:
    messaging_system: str
    broker_class: Type[BrokerUsecase]
    timeout: int = 3
    subscriber_kwargs: ClassVar[Dict[str, Any]] = {}

    @pytest.fixture()
    def raw_broker(self):
        return None

    def patch_broker(
        self, raw_broker: BrokerUsecase, broker: BrokerUsecase
    ) -> BrokerUsecase:
        return broker

    @pytest.fixture()
    def tracer_provider(self) -> TracerProvider:
        resource = Resource.create(
            attributes={
                "service.name": "faststream.test",
            },
        )
        tracer_provider = TracerProvider(resource=resource)
        return tracer_provider

    @pytest.fixture()
    def trace_exporter(self, tracer_provider: TracerProvider) -> InMemorySpanExporter:
        exporter = InMemorySpanExporter()
        tracer_provider.add_span_processor(SimpleSpanProcessor(exporter))
        return exporter

    def assert_span(
            self,
            span: Span,
            action: str,
            destination: str,
            msg: str,
            parent_span_id: Optional[str] = None,
    ) -> None:
        assert span.attributes[SpanAttributes.MESSAGING_SYSTEM] == self.messaging_system
        assert span.attributes[SpanAttributes.MESSAGING_MESSAGE_CONVERSATION_ID] == IsUUID
        assert span.name == f"{destination} {action}"
        assert span.kind in (SpanKind.CONSUMER, SpanKind.PRODUCER)

        if span.kind == SpanKind.PRODUCER and action in (MessageAction.CREATE, MessageAction.PUBLISH):
            assert span.attributes[SpanAttributes.MESSAGING_DESTINATION_NAME] == destination

        if span.kind == SpanKind.CONSUMER and action in (MessageAction.CREATE, MessageAction.PROCESS):
            assert span.attributes["messaging.destination_publish.name"] == destination
            assert span.attributes[SpanAttributes.MESSAGING_MESSAGE_ID] == IsUUID

        if action == MessageAction.PROCESS:
            assert span.attributes[SpanAttributes.MESSAGING_MESSAGE_PAYLOAD_SIZE_BYTES] == len(msg)

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
            tasks = (asyncio.create_task(broker.publish(msg, queue)), asyncio.create_task(event.wait()))
            await asyncio.wait(tasks, timeout=self.timeout)

        create, publish, process = cast("tuple[Span, Span, Span]", trace_exporter.get_finished_spans())
        parent_span_id = create.context.span_id

        self.assert_span(create, MessageAction.CREATE, queue, msg)
        self.assert_span(publish, MessageAction.PUBLISH, queue, msg, parent_span_id)
        self.assert_span(process, MessageAction.PROCESS, queue, msg, parent_span_id)

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
            tasks = (asyncio.create_task(broker.publish(msg, queue)), asyncio.create_task(event.wait()))
            await asyncio.wait(tasks, timeout=self.timeout)

        spans = trace_exporter.get_finished_spans()
        create, publish1, publish2, process1, process2 = cast("tuple[Span, Span, Span, Span, Span]", spans)
        parent_span_id = create.context.span_id

        self.assert_span(create, MessageAction.CREATE, first_queue, msg)
        self.assert_span(publish1, MessageAction.PUBLISH, first_queue, msg, parent_span_id)
        self.assert_span(process1, MessageAction.PROCESS, first_queue, msg, parent_span_id)
        self.assert_span(publish2, MessageAction.PUBLISH, second_queue, msg, process1.context.span_id)
        self.assert_span(process2, MessageAction.PROCESS, second_queue, msg, parent_span_id)

        assert create.end_time < publish1.end_time < publish2.end_time < process1.end_time < process2.end_time
        assert process1.start_time < publish2.start_time < publish2.end_time < process1.end_time

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
            tasks = (asyncio.create_task(broker.publish(msg, queue)), asyncio.create_task(event.wait()))
            await asyncio.wait(tasks, timeout=self.timeout)

        create, process = cast("tuple[Span, Span]", trace_exporter.get_finished_spans())
        parent_span_id = create.context.span_id

        self.assert_span(create, MessageAction.CREATE, queue, msg)
        self.assert_span(process, MessageAction.PROCESS, queue, msg, parent_span_id)

        assert event.is_set()
        mock.assert_called_once_with(msg)
