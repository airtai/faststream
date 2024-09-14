import asyncio
from typing import Any, Optional, Type
from unittest.mock import Mock, call, ANY

import pytest
from prometheus_client import CollectorRegistry

from faststream.broker.core.usecase import BrokerUsecase
from faststream.broker.message import AckStatus, StreamMessage
from faststream.prometheus.middleware import (
    PROCESSING_STATUS_BY_HANDLER_EXCEPTION_MAP,
    BasePrometheusMiddleware,
)
from faststream.prometheus.provider import MetricsSettingsProvider
from tests.brokers.base.basic import BaseTestcaseConfig


@pytest.mark.asyncio
class LocalPrometheusTestcase(BaseTestcaseConfig):
    broker_class: Type[BrokerUsecase]
    middleware_class: Type[BasePrometheusMiddleware]
    message_class: Type[StreamMessage[Any]]
    provider: MetricsSettingsProvider

    @pytest.fixture
    def registry(self):
        return CollectorRegistry()

    @staticmethod
    def consume_destination_name(queue: str) -> str:
        return queue

    @pytest.mark.parametrize("status", AckStatus)
    @pytest.mark.parametrize(
        "exception_class",
        [*list(PROCESSING_STATUS_BY_HANDLER_EXCEPTION_MAP.keys()), Exception, None],
    )
    async def test_subscriber_metrics(
        self,
        event: asyncio.Event,
        queue: str,
        registry: CollectorRegistry,
        status: AckStatus,
        exception_class: Optional[Type[Exception]],
    ):
        middleware = self.middleware_class(registry=registry)
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
        consume_attrs = self.provider.get_consume_attrs_from_message(message)
        assert metrics.received_messages.labels.mock_calls == [
            call(
                broker=self.provider.messaging_system,
                handler=consume_attrs["destination_name"],
            ),
            call().inc(),
        ]

        received_messages_size_labels_mock_calls = []

        for size in consume_attrs["messages_sizes"]:
            received_messages_size_labels_mock_calls.extend(
                [
                    call(
                        broker=self.provider.messaging_system,
                        handler=consume_attrs["destination_name"],
                    ),
                    call().observe(size),
                ]
            )

        assert (
            metrics.received_messages_size.labels.mock_calls
            == received_messages_size_labels_mock_calls
        )

        assert metrics.received_messages_in_process.labels.mock_calls == [
            call(
                broker=self.provider.messaging_system,
                handler=consume_attrs["destination_name"],
            ),
            call().inc(),
            call(
                broker=self.provider.messaging_system,
                handler=consume_attrs["destination_name"],
            ),
            call().dec(),
        ]

        assert metrics.received_messages_processing_time.labels.mock_calls == [
            call(
                broker=self.provider.messaging_system,
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
                broker=self.provider.messaging_system,
                handler=consume_attrs["destination_name"],
                status=status,
            ),
            call().inc(),
        ]

        if status == "error":
            assert metrics.messages_processing_exceptions.labels.mock_calls == [
                call(
                    broker=self.provider.messaging_system,
                    handler=consume_attrs["destination_name"],
                    exception_type=exception_class.__name__,
                ),
                call().inc(),
            ]

    def assert_publish_metrics(self, metrics: Any):
        assert metrics.messages_publish_time.labels.mock_calls == [
            call(broker=self.provider.messaging_system, destination=ANY),
            call().observe(ANY),
        ]
        assert metrics.published_messages.labels.mock_calls == [
            call(broker=self.provider.messaging_system, destination=ANY, status=ANY),
            call().inc(ANY),
        ]
