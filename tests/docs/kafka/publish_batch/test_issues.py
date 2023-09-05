from typing import List

import pytest

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker, TestKafkaBroker

broker = KafkaBroker()
batch_producer = broker.publisher("response", batch=True)


@batch_producer
@broker.subscriber("test")
async def handle(msg: str) -> List[int]:
    return [1, 2, 3]


# when the following block is uncomment, the test passes
# TODO: remove after https://github.com/airtai/fastkafka/pull/533 merged
@broker.subscriber("response", batch=True)
async def handle_response(msg: List[int], logger: Logger):
    logger.info(msg)


app = FastStream(broker)


@pytest.mark.asyncio
async def test_base_app():
    async with TestKafkaBroker(broker):
        await broker.publish("", "test")
