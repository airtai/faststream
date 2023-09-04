import pytest

from faststream.kafka import TestKafkaBroker
from docs_src.kafka.batch_consuming_primitives.app import (
    broker, 
    on_hello_world, 
    HelloWorld,
    app
)

@pytest.mark.asyncio
async def test_me():
    async with TestKafkaBroker(broker) as test_broker:
        # This works
        await test_broker.publish("123", "test")

        # why is this failing?
        with pytest.raises(Exception) as e:
            await test_broker.publish("I", "test_batch")
            await test_broker.publish("am", "test_batch")
            await test_broker.publish("FastStream", "test_batch")

            # In the end we should be able to assert something like this
            handle_batch.mock.assert_called_once_with(["I", "am", "FastStream"])