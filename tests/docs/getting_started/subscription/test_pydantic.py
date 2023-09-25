import pytest

from faststream.kafka import TestKafkaBroker
from faststream.rabbit import TestRabbitBroker


@pytest.mark.asyncio
async def test_pydantic_model_rabbit():
    from docs.docs_src.getting_started.subscription.pydantic_model_rabbit import (
        broker,
        handle,
    )

    async with TestRabbitBroker(broker) as br:
        await br.publish({"name": "John", "user_id": 1}, "test-queue")
        handle.mock.assert_called_once_with({"name": "John", "user_id": 1})


@pytest.mark.asyncio
async def test_pydantic_model_kafka():
    from docs.docs_src.getting_started.subscription.pydantic_model_kafka import (
        broker,
        handle,
    )

    async with TestKafkaBroker(broker) as br:
        await br.publish({"name": "John", "user_id": 1}, "test-topic")
        handle.mock.assert_called_once_with({"name": "John", "user_id": 1})
