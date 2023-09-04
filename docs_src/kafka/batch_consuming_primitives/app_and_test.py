from typing import List

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker, TestKafkaBroker

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


@broker.subscriber("test_batch", batch=True)
async def handle_batch(msg: List[str], logger: Logger):
    logger.info(msg)


import pytest


@pytest.mark.asyncio
async def test_me():
    async with TestKafkaBroker(broker) as test_broker:
        await test_broker.publish_batch("I", "am", "FastStream", topic="test_batch")
        handle_batch.mock.assert_called_with(["I", "am", "FastStream"])
