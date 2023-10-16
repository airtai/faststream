import pytest
from pydantic import ValidationError

from faststream.kafka import TestKafkaBroker, KafkaBroker

from .annotation_kafka import broker, handle


@pytest.mark.asyncio
async def test_handle():
    async with TestKafkaBroker(broker) as br:
        await br.publish({"name": "John", "user_id": 1}, topic="test-topic")

        handle.mock.assert_called_once_with({"name": "John", "user_id": 1})

    assert handle.mock is None

@pytest.mark.asyncio
async def test_validation_error():
    async with TestKafkaBroker(broker) as br:
        with pytest.raises(ValidationError):
            await br.publish("wrong message", topic="test-topic")

        handle.mock.assert_called_once_with("wrong message")


@pytest.mark.asyncio()
async def test_handle_single_kwarg():
    broker = KafkaBroker()

    @broker.subscriber("test-topic")
    async def handle(name: str):
        assert name == "John"

    async with TestKafkaBroker(broker) as br:
        await br.publish({"name": "John"}, topic="test-topic")

        handle.mock.assert_called_once_with({"name": "John"})

    assert handle.mock is None
