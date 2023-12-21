import pytest

from faststream import TestApp
from faststream.kafka import TestKafkaBroker
from faststream.nats import TestNatsBroker
from faststream.rabbit import TestRabbitBroker
from faststream.redis import TestRedisBroker


@pytest.mark.asyncio()
async def test_broker_kafka():
    from docs.docs_src.getting_started.publishing.kafka.broker import (
        app,
        broker,
        handle,
        handle_next,
    )

    async with TestKafkaBroker(broker), TestApp(app):
        handle.mock.assert_called_once_with("")
        handle_next.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio()
async def test_broker_rabbit():
    from docs.docs_src.getting_started.publishing.rabbit.broker import (
        app,
        broker,
        handle,
        handle_next,
    )

    async with TestRabbitBroker(broker), TestApp(app):
        handle.mock.assert_called_once_with("")
        handle_next.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio()
async def test_broker_nats():
    from docs.docs_src.getting_started.publishing.nats.broker import (
        app,
        broker,
        handle,
        handle_next,
    )

    async with TestNatsBroker(broker), TestApp(app):
        handle.mock.assert_called_once_with("")
        handle_next.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio()
async def test_broker_redis():
    from docs.docs_src.getting_started.publishing.redis.broker import (
        app,
        broker,
        handle,
        handle_next,
    )

    async with TestRedisBroker(broker), TestApp(app):
        handle.mock.assert_called_once_with("")
        handle_next.mock.assert_called_once_with("Hi!")
