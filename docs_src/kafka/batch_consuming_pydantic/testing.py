import pytest

from faststream.kafka import TestKafkaBroker
from docs_src.kafka.batch_consuming.app import (
    broker, 
    on_hello_world, 
    HelloWorld,
    app
)

@pytest.mark.asyncio
@app.after_startup
async def test_base_app():
    async with TestKafkaBroker(broker) as test_broker:
        #await test_broker.publish("First Hello", "hello_world")
        #await test_broker.publish("Sec Hello", "hello_world")
        await test_broker.publish(HelloWorld(msg="Second Hello"), "hello_world")

        #on_hello_world.mock.assert_called_with(dict([HelloWorld(msg="First Hello")]))
        
        on_hello_world.mock.assert_called()
        #on_hello_world.mock.assert_called_with(dict(msg=["First Hello"]))
        