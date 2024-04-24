import asyncio
from typing import Any, ClassVar, Dict, Type
from unittest.mock import Mock

import pytest
from dirty_equals import IsUUID
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.semconv.trace import SpanAttributes

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
            await asyncio.wait(
                (
                    asyncio.create_task(broker.publish(msg, queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=self.timeout,
            )

        create, publish, process = trace_exporter.get_finished_spans()
        parent_span_id = create.context.span_id

        assert (
            create.attributes.get(SpanAttributes.MESSAGING_SYSTEM)
            == self.messaging_system
        )
        assert create.attributes.get(SpanAttributes.MESSAGING_DESTINATION_NAME) == queue
        assert (
            create.attributes.get(SpanAttributes.MESSAGING_MESSAGE_CONVERSATION_ID)
            == IsUUID
        )
        assert create.name == f"{queue} {MessageAction.CREATE}"

        assert (
            publish.attributes.get(SpanAttributes.MESSAGING_SYSTEM)
            == self.messaging_system
        )
        assert (
            publish.attributes.get(SpanAttributes.MESSAGING_DESTINATION_NAME) == queue
        )
        assert (
            publish.attributes.get(SpanAttributes.MESSAGING_MESSAGE_CONVERSATION_ID)
            == IsUUID
        )
        assert publish.name == f"{queue} {MessageAction.PUBLISH}"
        assert publish.parent.span_id == parent_span_id

        assert (
            process.attributes.get(SpanAttributes.MESSAGING_SYSTEM)
            == self.messaging_system
        )
        assert process.attributes.get("messaging.destination_publish.name") == queue
        assert (
            process.attributes.get(SpanAttributes.MESSAGING_MESSAGE_CONVERSATION_ID)
            == IsUUID
        )
        assert process.attributes.get(SpanAttributes.MESSAGING_MESSAGE_ID) == IsUUID
        assert process.attributes.get(
            SpanAttributes.MESSAGING_MESSAGE_PAYLOAD_SIZE_BYTES
        ) == len(msg)
        assert process.name == f"{queue} {MessageAction.PROCESS}"
        assert process.parent.span_id == parent_span_id

        assert event.is_set()
        mock.assert_called_once_with(msg)


@pytest.mark.asyncio()
class TelemetryTestcase(LocalTelemetryTestcase):
    pass
