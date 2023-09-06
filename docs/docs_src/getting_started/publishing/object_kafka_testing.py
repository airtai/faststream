from faststream.kafka import TestKafkaBroker
import pytest

from .object_kafka import publisher, broker


@pytest.mark.asyncio
async def test_handle():
    async with TestKafkaBroker(broker) as br:
        await br.publish("", topic="test-topic")

        publisher.mock.assert_called_once_with("Hi!")
