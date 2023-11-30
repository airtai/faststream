import pytest

from faststream.kafka import TestKafkaBroker
from faststream.nats import TestNatsBroker
from faststream.rabbit import TestRabbitBroker
from faststream.redis import TestRedisBroker


@pytest.mark.asyncio
async def test_base_kafka():
    from docs.docs_src.getting_started.context.kafka.base import base_handler, broker

    async with TestKafkaBroker(broker) as br:
        await br.publish("Hi!", "test")

        base_handler.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio
async def test_base_rabbit():
    from docs.docs_src.getting_started.context.rabbit.base import base_handler, broker

    async with TestRabbitBroker(broker) as br:
        await br.publish("Hi!", "test")

        base_handler.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio
async def test_base_nats():
    from docs.docs_src.getting_started.context.nats.base import base_handler, broker

    async with TestNatsBroker(broker) as br:
        await br.publish("Hi!", "test")

        base_handler.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio
async def test_base_redis():
    from docs.docs_src.getting_started.context.redis.base import base_handler, broker

    async with TestRedisBroker(broker) as br:
        await br.publish("Hi!", "test")

        base_handler.mock.assert_called_once_with("Hi!")
