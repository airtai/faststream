from typing import List

import pytest

from faststream import FastStream
from faststream.confluent import KafkaBroker, TestKafkaBroker

broker = KafkaBroker()
batch_producer = broker.publisher("response", batch=True)


@batch_producer
@broker.subscriber("test")
async def handle(msg: str) -> List[int]:
    return [1, 2, 3]


app = FastStream(broker)


@pytest.mark.asyncio
async def test_base_app():
    async with TestKafkaBroker(broker):
        await broker.publish("", "test")
