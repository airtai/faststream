import pytest

from faststream.kafka import TestKafkaBroker

from .app import HelloWorld, broker, handle_batch


@pytest.mark.asyncio
async def test_me():
    async with TestKafkaBroker(broker):
        await broker.publish_batch(
            HelloWorld(msg="First Hello"),
            HelloWorld(msg="Second Hello"),
            topic="test_batch",
        )
        handle_batch.mock.assert_called_with(
            [dict(HelloWorld(msg="First Hello")), dict(HelloWorld(msg="Second Hello"))]
        )
