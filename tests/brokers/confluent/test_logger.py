import logging

import pytest

from faststream.confluent import KafkaBroker

from .basic import ConfluentTestcaseConfig


@pytest.mark.confluent
class TestLogger(ConfluentTestcaseConfig):
    """A class to represent a test Kafka broker."""

    @pytest.mark.asyncio
    async def test_custom_logger(self, queue: str):
        test_logger = logging.getLogger("test_logger")
        broker = KafkaBroker(logger=test_logger)

        args, kwargs = self.get_subscriber_params(queue)

        @broker.subscriber(*args, **kwargs)
        def subscriber(m): ...

        await broker.start()
        async with broker:
            for sub in broker._subscribers.values():
                consumer_logger = sub.consumer.logger
                assert consumer_logger == test_logger

            producer_logger = broker._producer._producer.logger
            assert producer_logger == test_logger
