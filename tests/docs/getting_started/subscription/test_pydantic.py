import pytest

from faststream.kafka import TestKafkaBroker
from faststream.nats import TestNatsBroker
from faststream.rabbit import TestRabbitBroker
from faststream.redis import TestRedisBroker


@pytest.mark.asyncio
async def test_pydantic_model_rabbit():
    from docs.docs_src.getting_started.subscription.rabbit.pydantic_model import (
        broker,
        handle,
    )

    async with TestRabbitBroker(broker) as br:
        await br.publish({"name": "John", "user_id": 1}, "test-queue")
        handle.mock.assert_called_once_with({"name": "John", "user_id": 1})


@pytest.mark.asyncio
async def test_pydantic_model_kafka():
    from docs.docs_src.getting_started.subscription.kafka.pydantic_model import (
        broker,
        handle,
    )

    async with TestKafkaBroker(broker) as br:
        await br.publish({"name": "John", "user_id": 1}, "test-topic")
        handle.mock.assert_called_once_with({"name": "John", "user_id": 1})


@pytest.mark.asyncio
async def test_pydantic_model_nats():
    from docs.docs_src.getting_started.subscription.nats.pydantic_model import (
        broker,
        handle,
    )

    async with TestNatsBroker(broker) as br:
        await br.publish({"name": "John", "user_id": 1}, "test-subject")
        handle.mock.assert_called_once_with({"name": "John", "user_id": 1})


@pytest.mark.asyncio
async def test_pydantic_model_redis():
    from docs.docs_src.getting_started.subscription.redis.pydantic_model import (
        broker,
        handle,
    )

    async with TestRedisBroker(broker) as br:
        await br.publish({"name": "John", "user_id": 1}, "test-channel")
        handle.mock.assert_called_once_with({"name": "John", "user_id": 1})
