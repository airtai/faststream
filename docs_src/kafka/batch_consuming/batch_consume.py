from typing import List

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker, TestKafkaBroker

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


@broker.subscriber("test")
async def handle(msg: str, logger: Logger):
    logger.info(msg)

@broker.subscriber("test_batch", batch=True)
async def handle_batch(msg: List[str], logger: Logger):
    logger.info(msg)

import pytest

@pytest.mark.asyncio
async def test_me():
    async with TestKafkaBroker(broker) as test_broker:
        await test_broker.publish("123", "test")

        # why is this failing?
        with pytest.raises(Exception) as e:
            await test_broker.publish("123", "test_batch")
