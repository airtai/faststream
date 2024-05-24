import asyncio
import logging
from typing import Any, ClassVar, Dict

import pytest

from faststream.broker.core.usecase import BrokerUsecase
from faststream.confluent import KafkaBroker


@pytest.mark.confluent()
class TestLogger:
    """A class to represent a test Kafka broker."""

    timeout: int = 10
    subscriber_kwargs: ClassVar[Dict[str, Any]] = {"auto_offset_reset": "earliest"}

    def get_broker(self, apply_types: bool = False):
        return KafkaBroker(apply_types=apply_types)

    def patch_broker(self, broker: BrokerUsecase[Any, Any]) -> BrokerUsecase[Any, Any]:
        return broker

    @pytest.mark.asyncio()
    async def test_custom_logger(
        self,
        queue: str,
        event: asyncio.Event,
    ):
        test_logger = logging.getLogger("test_logger")
        consume_broker = KafkaBroker(logger=test_logger)

        @consume_broker.subscriber(queue, **self.subscriber_kwargs)
        def subscriber(m):
            event.set()

        async with self.patch_broker(consume_broker) as br:
            await br.start()

            await br.publish_batch(1, "hi", topic=queue)

            # ToDo: Fetch consumer logger and assert it

            producer_logger = br._producer._producer.logger
            assert producer_logger == test_logger

            await asyncio.wait(
                (
                    asyncio.create_task(br.publish("hello", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=self.timeout,
            )

        assert event.is_set()
