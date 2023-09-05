from typing import List, Tuple
from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker

broker = KafkaBroker()
batch_producer = broker.publisher("response", batch=True)

@batch_producer
@broker.subscriber("test")
async def handle(msg: str) -> List[int]:
    return [1, 2, 3]

# when the following block is uncomment, the test passes
@broker.subscriber("response", batch=True)
async def handle_response(msg: List[int], logger: Logger):
    logger.info(msg)

app = FastStream(broker)

import pytest

from faststream.kafka import TestKafkaBroker


@pytest.mark.asyncio
async def test_base_app():
    async with TestKafkaBroker(broker):
        await broker.publish("", "test")

