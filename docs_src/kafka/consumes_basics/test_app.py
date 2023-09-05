import pytest

from faststream.kafka import TestKafkaBroker

from .app import (
    HelloWorld,
    broker,
    on_hello_world,
)


@pytest.mark.asyncio
async def test_base_app():
    async with TestKafkaBroker(broker):
        await broker.publish(HelloWorld(msg="First Hello"), "hello_world")
        on_hello_world.mock.assert_called_with(dict(HelloWorld(msg="First Hello")))
