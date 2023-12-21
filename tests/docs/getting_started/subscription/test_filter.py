import pytest

from faststream import TestApp
from faststream.kafka import TestKafkaBroker
from faststream.nats import TestNatsBroker
from faststream.rabbit import TestRabbitBroker
from faststream.redis import TestRedisBroker


@pytest.mark.asyncio()
async def test_kafka_filtering():
    from docs.docs_src.getting_started.subscription.kafka.filter import (
        app,
        broker,
        default_handler,
        handle,
    )

    async with TestKafkaBroker(broker), TestApp(app):
        handle.mock.assert_called_once_with({"name": "John", "user_id": 1})
        default_handler.mock.assert_called_once_with("Hello, FastStream!")


@pytest.mark.asyncio()
async def test_rabbit_filtering():
    from docs.docs_src.getting_started.subscription.rabbit.filter import (
        app,
        broker,
        default_handler,
        handle,
    )

    async with TestRabbitBroker(broker), TestApp(app):
        handle.mock.assert_called_once_with({"name": "John", "user_id": 1})
        default_handler.mock.assert_called_once_with("Hello, FastStream!")


@pytest.mark.asyncio()
async def test_nats_filtering():
    from docs.docs_src.getting_started.subscription.nats.filter import (
        app,
        broker,
        default_handler,
        handle,
    )

    async with TestNatsBroker(broker), TestApp(app):
        handle.mock.assert_called_once_with({"name": "John", "user_id": 1})
        default_handler.mock.assert_called_once_with("Hello, FastStream!")


@pytest.mark.asyncio()
async def test_redis_filtering():
    from docs.docs_src.getting_started.subscription.redis.filter import (
        app,
        broker,
        default_handler,
        handle,
    )

    async with TestRedisBroker(broker), TestApp(app):
        handle.mock.assert_called_once_with({"name": "John", "user_id": 1})
        default_handler.mock.assert_called_once_with("Hello, FastStream!")
