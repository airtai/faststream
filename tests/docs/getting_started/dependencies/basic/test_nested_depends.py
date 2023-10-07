import pytest

from faststream.kafka import TestKafkaBroker
from faststream.nats import TestNatsBroker
from faststream.rabbit import TestRabbitBroker


@pytest.mark.asyncio
async def test_nested_depends_kafka():
    from docs.docs_src.getting_started.dependencies.basic.kafka.nested_depends import (
        broker,
        handler,
    )

    async with TestKafkaBroker(broker):
        await broker.publish({}, "test")
        handler.mock.assert_called_once_with({})


@pytest.mark.asyncio
async def test_nested_depends_rabbit():
    from docs.docs_src.getting_started.dependencies.basic.rabbit.nested_depends import (
        broker,
        handler,
    )

    async with TestRabbitBroker(broker):
        await broker.publish({}, "test")
        handler.mock.assert_called_once_with({})


@pytest.mark.asyncio
async def test_nested_depends_nats():
    from docs.docs_src.getting_started.dependencies.basic.nats.nested_depends import (
        broker,
        handler,
    )

    async with TestNatsBroker(broker):
        await broker.publish({}, "test")
        handler.mock.assert_called_once_with({})
