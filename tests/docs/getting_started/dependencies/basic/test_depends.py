import pytest

from faststream.kafka import TestKafkaBroker
from faststream.nats import TestNatsBroker
from faststream.rabbit import TestRabbitBroker


@pytest.mark.asyncio
async def test_depends_kafka():
    from docs.docs_src.getting_started.dependencies.basic.kafka.depends import (
        broker,
        handler,
    )

    async with TestKafkaBroker(broker):
        await broker.publish({}, "test")
        handler.mock.assert_called_once_with({})


@pytest.mark.asyncio
async def test_depends_rabbit():
    from docs.docs_src.getting_started.dependencies.basic.rabbit.depends import (
        broker,
        handler,
    )

    async with TestRabbitBroker(broker):
        await broker.publish({}, "test")
        handler.mock.assert_called_once_with({})


@pytest.mark.asyncio
async def test_depends_nats():
    from docs.docs_src.getting_started.dependencies.basic.nats.depends import (
        broker,
        handler,
    )

    async with TestNatsBroker(broker):
        await broker.publish({}, "test")
        handler.mock.assert_called_once_with({})
