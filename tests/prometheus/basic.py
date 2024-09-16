import asyncio
from typing import Any, Optional, Type
from unittest.mock import ANY, Mock, call

import pytest
from prometheus_client import CollectorRegistry

from faststream.broker.core.usecase import BrokerUsecase
from faststream.broker.message import AckStatus, StreamMessage
from faststream.prometheus.middleware import (
    PROCESSING_STATUS_BY_HANDLER_EXCEPTION_MAP,
    BasePrometheusMiddleware,
)
from tests.brokers.base.basic import BaseTestcaseConfig


@pytest.mark.asyncio
class LocalPrometheusTestcase(BaseTestcaseConfig):
    broker_class: Type[BrokerUsecase]
    middleware_class: Type[BasePrometheusMiddleware]
    message_class: Type[StreamMessage[Any]]

    @staticmethod
    def consume_destination_name(queue: str) -> str:
        return queue

    @property
    def settings_provider_factory(self):
        return self.middleware_class(
            registry=CollectorRegistry()
        )._settings_provider_factory

    @pytest.mark.parametrize("status", AckStatus)
    @pytest.mark.parametrize(
        "exception_class",
        [*list(PROCESSING_STATUS_BY_HANDLER_EXCEPTION_MAP.keys()), Exception, None],
    )
    async def test_metrics(
        self,
        event: asyncio.Event,
        queue: str,
        status: AckStatus,
        exception_class: Optional[Type[Exception]],
    ):
        middleware = self.middleware_class(registry=CollectorRegistry())
        metrics_mock = Mock()
        middleware._metrics = metrics_mock

        broker = self.broker_class(middlewares=(middleware,))

        args, kwargs = self.get_subscriber_params(queue)

        message_class = self.message_class
        message = None

        @broker.subscriber(*args, **kwargs)
        async def handler(m: message_class):
            event.set()

            nonlocal message
            message = m

            if exception_class:
                raise exception_class

            if status == AckStatus.acked:
                await message.ack()
            elif status == AckStatus.nacked:
                await message.nack()
            elif status == AckStatus.rejected:
                await message.reject()

        async with broker:
            await broker.start()
            tasks = (
                asyncio.create_task(broker.publish("hello", queue)),
                asyncio.create_task(event.wait()),
            )
            await asyncio.wait(tasks, timeout=self.timeout)

        assert event.is_set()
        self.assert_consume_metrics(
            metrics=metrics_mock, message=message, exception_class=exception_class
        )
        self.assert_publish_metrics(metrics=metrics_mock)

    def assert_consume_metrics(
        self,
        *,
        metrics: Any,
        message: Any,
        exception_class: Optional[Type[Exception]],
    ):
        settings_provider = self.settings_provider_factory(message.raw_message)
        consume_attrs = settings_provider.get_consume_attrs_from_message(message)
        assert metrics.received_messages.labels.mock_calls == [
            call(
                broker=settings_provider.messaging_system,
                handler=consume_attrs["destination_name"],
            ),
            call().inc(consume_attrs["messages_count"]),
        ]

        assert metrics.received_messages_size.labels.mock_calls == [
            call(
                broker=settings_provider.messaging_system,
                handler=consume_attrs["destination_name"],
            ),
            call().observe(consume_attrs["message_size"]),
        ]

        assert metrics.received_messages_in_process.labels.mock_calls == [
            call(
                broker=settings_provider.messaging_system,
                handler=consume_attrs["destination_name"],
            ),
            call().inc(),
            call(
                broker=settings_provider.messaging_system,
                handler=consume_attrs["destination_name"],
            ),
            call().dec(),
        ]

        assert metrics.received_messages_processing_time.labels.mock_calls == [
            call(
                broker=settings_provider.messaging_system,
                handler=consume_attrs["destination_name"],
            ),
            call().observe(ANY),
        ]

        if exception_class:
            status = (
                PROCESSING_STATUS_BY_HANDLER_EXCEPTION_MAP.get(exception_class)
                or "error"
            )
        else:
            status = message.committed.value

        assert metrics.received_processed_messages.labels.mock_calls == [
            call(
                broker=settings_provider.messaging_system,
                handler=consume_attrs["destination_name"],
                status=status,
            ),
            call().inc(),
        ]

        if status == "error":
            assert metrics.messages_processing_exceptions.labels.mock_calls == [
                call(
                    broker=settings_provider.messaging_system,
                    handler=consume_attrs["destination_name"],
                    exception_type=exception_class.__name__,
                ),
                call().inc(),
            ]

    def assert_publish_metrics(self, metrics: Any):
        settings_provider = self.settings_provider_factory(None)
        assert metrics.messages_publish_time.labels.mock_calls == [
            call(broker=settings_provider.messaging_system, destination=ANY),
            call().observe(ANY),
        ]
        assert metrics.published_messages.labels.mock_calls == [
            call(
                broker=settings_provider.messaging_system,
                destination=ANY,
                status="success",
            ),
            call().inc(ANY),
        ]
