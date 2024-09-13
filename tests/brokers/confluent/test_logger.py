import asyncio
import logging
from typing import Any

import pytest

from faststream._internal.broker.broker import BrokerUsecase
from faststream.confluent import KafkaBroker

from .basic import ConfluentTestcaseConfig


@pytest.mark.confluent
class TestLogger(ConfluentTestcaseConfig):
    """A class to represent a test Kafka broker."""

    def get_broker(self, apply_types: bool = False):
        return KafkaBroker(apply_types=apply_types)

    def patch_broker(self, broker: BrokerUsecase[Any, Any]) -> BrokerUsecase[Any, Any]:
        return broker

    @pytest.mark.asyncio
    async def test_custom_logger(
        self,
        queue: str,
        event: asyncio.Event,
    ):
        test_logger = logging.getLogger("test_logger")
        consume_broker = KafkaBroker(logger=test_logger)

        args, kwargs = self.get_subscriber_params(queue)

        @consume_broker.subscriber(*args, **kwargs)
        def subscriber(m):
            event.set()

        async with self.patch_broker(consume_broker) as br:
            await br.start()

            for sub in br._subscribers.values():
                consumer_logger = sub.consumer.logger
                assert consumer_logger == test_logger

            producer_logger = br._producer._producer.logger
            assert producer_logger == test_logger

            await asyncio.wait(
                (
                    asyncio.create_task(br.publish("hello", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=10,
            )

        assert event.is_set()
