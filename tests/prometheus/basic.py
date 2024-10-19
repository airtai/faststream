import asyncio
from typing import Any, Optional, Type
from unittest.mock import ANY, Mock, call

import pytest
from prometheus_client import CollectorRegistry

from faststream import Context
from faststream.broker.message import AckStatus
from faststream.exceptions import RejectMessage
from faststream.prometheus.middleware import (
    PROCESSING_STATUS_BY_ACK_STATUS,
    PROCESSING_STATUS_BY_HANDLER_EXCEPTION_MAP,
)
from faststream.prometheus.types import ProcessingStatus
from tests.brokers.base.basic import BaseTestcaseConfig


@pytest.mark.asyncio
class LocalPrometheusTestcase(BaseTestcaseConfig):
    def get_broker(self, apply_types=False, **kwargs):
        raise NotImplementedError

    def get_middleware(self, **kwargs):
        raise NotImplementedError

    @staticmethod
    def consume_destination_name(queue: str) -> str:
        return queue

    @property
    def settings_provider_factory(self):
        return self.get_middleware(
            registry=CollectorRegistry()
        )._settings_provider_factory

    @pytest.mark.parametrize(
        (
            "status",
            "exception_class",
        ),
        [
            pytest.param(
                AckStatus.acked,
                RejectMessage,
                id="acked status with reject message exception",
            ),
            pytest.param(
                AckStatus.acked, Exception, id="acked status with not handler exception"
            ),
            pytest.param(AckStatus.acked, None, id="acked status without exception"),
            pytest.param(AckStatus.nacked, None, id="nacked status without exception"),
            pytest.param(
                AckStatus.rejected, None, id="rejected status without exception"
            ),
        ],
    )
    async def test_metrics(
        self,
        event: asyncio.Event,
        queue: str,
        status: AckStatus,
        exception_class: Optional[Type[Exception]],
    ):
        middleware = self.get_middleware(registry=CollectorRegistry())
        metrics_manager_mock = Mock()
        middleware._metrics_manager = metrics_manager_mock

        broker = self.get_broker(apply_types=True, middlewares=(middleware,))

        args, kwargs = self.get_subscriber_params(queue)

        message = None

        @broker.subscriber(*args, **kwargs)
        async def handler(m=Context("message")):
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
            metrics_manager=metrics_manager_mock,
            message=message,
            exception_class=exception_class,
        )
        self.assert_publish_metrics(metrics_manager=metrics_manager_mock)

    def assert_consume_metrics(
        self,
        *,
        metrics_manager: Any,
        message: Any,
        exception_class: Optional[Type[Exception]],
    ):
        settings_provider = self.settings_provider_factory(message.raw_message)
        consume_attrs = settings_provider.get_consume_attrs_from_message(message)
        assert metrics_manager.add_received_message.mock_calls == [
            call(
                amount=consume_attrs["messages_count"],
                broker=settings_provider.messaging_system,
                handler=consume_attrs["destination_name"],
            ),
        ]

        assert metrics_manager.observe_received_messages_size.mock_calls == [
            call(
                size=consume_attrs["message_size"],
                broker=settings_provider.messaging_system,
                handler=consume_attrs["destination_name"],
            ),
        ]

        assert metrics_manager.add_received_message_in_process.mock_calls == [
            call(
                amount=consume_attrs["messages_count"],
                broker=settings_provider.messaging_system,
                handler=consume_attrs["destination_name"],
            ),
        ]
        assert metrics_manager.remove_received_message_in_process.mock_calls == [
            call(
                amount=consume_attrs["messages_count"],
                broker=settings_provider.messaging_system,
                handler=consume_attrs["destination_name"],
            )
        ]

        assert (
            metrics_manager.observe_received_processed_message_duration.mock_calls
            == [
                call(
                    duration=ANY,
                    broker=settings_provider.messaging_system,
                    handler=consume_attrs["destination_name"],
                ),
            ]
        )

        status = ProcessingStatus.acked

        if exception_class:
            status = (
                PROCESSING_STATUS_BY_HANDLER_EXCEPTION_MAP.get(exception_class)
                or ProcessingStatus.error
            )
        elif message.committed:
            status = PROCESSING_STATUS_BY_ACK_STATUS[message.committed]

        assert metrics_manager.add_received_processed_message.mock_calls == [
            call(
                amount=consume_attrs["messages_count"],
                broker=settings_provider.messaging_system,
                handler=consume_attrs["destination_name"],
                status=status.value,
            ),
        ]

        if status == ProcessingStatus.error:
            assert (
                metrics_manager.add_received_processed_message_exception.mock_calls
                == [
                    call(
                        broker=settings_provider.messaging_system,
                        handler=consume_attrs["destination_name"],
                        exception_type=exception_class.__name__,
                    ),
                ]
            )

    def assert_publish_metrics(self, metrics_manager: Any):
        settings_provider = self.settings_provider_factory(None)
        assert metrics_manager.observe_published_message_duration.mock_calls == [
            call(
                duration=ANY, broker=settings_provider.messaging_system, destination=ANY
            ),
        ]
        assert metrics_manager.add_published_message.mock_calls == [
            call(
                amount=ANY,
                broker=settings_provider.messaging_system,
                destination=ANY,
                status="success",
            ),
        ]
