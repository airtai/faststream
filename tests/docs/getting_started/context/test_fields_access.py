import pytest

from faststream.kafka import TestKafkaBroker
from faststream.nats import TestNatsBroker
from faststream.rabbit import TestRabbitBroker
from faststream.redis import TestRedisBroker


@pytest.mark.asyncio
async def test_fields_access_kafka():
    from docs.docs_src.getting_started.context.kafka.fields_access import (
        broker,
        handle,
    )

    async with TestKafkaBroker(broker) as br:
        await br.publish("Hi!", "test-topic", headers={"user": "John"})

        handle.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio
async def test_fields_access_rabbit():
    from docs.docs_src.getting_started.context.rabbit.fields_access import (
        broker,
        handle,
    )

    async with TestRabbitBroker(broker) as br:
        await br.publish("Hi!", "test-queue", headers={"user": "John"})

        handle.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio
async def test_fields_access_nats():
    from docs.docs_src.getting_started.context.nats.fields_access import (
        broker,
        handle,
    )

    async with TestNatsBroker(broker) as br:
        await br.publish("Hi!", "test-subject", headers={"user": "John"})

        handle.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio
async def test_fields_access_redis():
    from docs.docs_src.getting_started.context.redis.fields_access import (
        broker,
        handle,
    )

    async with TestRedisBroker(broker) as br:
        await br.publish("Hi!", "test-channel", headers={"user": "John"})

        handle.mock.assert_called_once_with("Hi!")
