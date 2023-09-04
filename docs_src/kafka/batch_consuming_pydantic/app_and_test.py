from typing import List
from pydantic import BaseModel, Field

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker, TestKafkaBroker

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


class HelloWorld(BaseModel):
    msg: str = Field(
        ...,
        examples=["Hello"],
        description="Demo hello world message",
    )

@broker.subscriber("test_batch", batch=True)
async def handle_batch(msg: List[HelloWorld], logger: Logger):
    logger.info(msg)


import pytest


@pytest.mark.asyncio
async def test_me():
    async with TestKafkaBroker(broker) as test_broker:
        await test_broker.publish_batch(HelloWorld(msg="First Hello"), HelloWorld(msg="Second Hello"), topic="test_batch")
        handle_batch.mock.assert_called_with([dict(HelloWorld(msg="First Hello")), dict(HelloWorld(msg="Second Hello"))])
