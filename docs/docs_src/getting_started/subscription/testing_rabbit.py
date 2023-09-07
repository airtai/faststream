import pytest

from faststream.rabbit import TestRabbitBroker

from .annotation_rabbit import broker, handle


@pytest.mark.asyncio
async def test_handle():
    async with TestRabbitBroker(broker) as br:
        await br.publish({"name": "john", "user_id": 1}, queue="test-queue")

        handle.mock.assert_called_once_with({"name": "john", "user_id": 1})
