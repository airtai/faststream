import pytest

from faststream.kafka import TestKafkaBroker
from docs_src.kafka.consumes_basics.app import (
    broker, 
    on_hello_world, 
    HelloWorld,
)

@pytest.mark.asyncio
async def test_base_app():
    async with TestKafkaBroker(broker) as test_broker:
        await test_broker.publish(HelloWorld(msg="First Hello"), "hello_world")
        on_hello_world.mock.assert_called_with(dict(HelloWorld(msg="First Hello")))
        