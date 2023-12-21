import pytest

from faststream.kafka import TestKafkaBroker
from faststream.nats import TestNatsBroker
from faststream.rabbit import TestRabbitBroker
from faststream.redis import TestRedisBroker
from tests.marks import python39


@python39
@pytest.mark.asyncio()
async def test_annotated_kafka():
    from docs.docs_src.getting_started.context.kafka.annotated import (
        base_handler,
        broker,
    )

    async with TestKafkaBroker(broker) as br:
        await br.publish("Hi!", "test")

        base_handler.mock.assert_called_once_with("Hi!")


@python39
@pytest.mark.asyncio()
async def test_annotated_rabbit():
    from docs.docs_src.getting_started.context.rabbit.annotated import (
        base_handler,
        broker,
    )

    async with TestRabbitBroker(broker) as br:
        await br.publish("Hi!", "test")

        base_handler.mock.assert_called_once_with("Hi!")


@python39
@pytest.mark.asyncio()
async def test_annotated_nats():
    from docs.docs_src.getting_started.context.nats.annotated import (
        base_handler,
        broker,
    )

    async with TestNatsBroker(broker) as br:
        await br.publish("Hi!", "test")

        base_handler.mock.assert_called_once_with("Hi!")


@python39
@pytest.mark.asyncio()
async def test_annotated_redis():
    from docs.docs_src.getting_started.context.redis.annotated import (
        base_handler,
        broker,
    )

    async with TestRedisBroker(broker) as br:
        await br.publish("Hi!", "test")

        base_handler.mock.assert_called_once_with("Hi!")
