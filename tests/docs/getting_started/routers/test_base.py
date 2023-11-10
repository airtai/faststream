import pytest

from faststream import TestApp
from faststream.kafka import TestKafkaBroker
from faststream.nats import TestNatsBroker
from faststream.rabbit import TestRabbitBroker
from faststream.redis import TestRedisBroker


@pytest.mark.asyncio
async def test_base_router_kafka():
    from docs.docs_src.getting_started.routers.kafka.router import (
        app,
        broker,
        handle,
        handle_response,
    )

    async with TestKafkaBroker(broker), TestApp(app):
        handle.mock.assert_called_once_with({"name": "John", "user_id": 1})
        handle_response.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio
async def test_base_router_rabbit():
    from docs.docs_src.getting_started.routers.rabbit.router import (
        app,
        broker,
        handle,
        handle_response,
    )

    async with TestRabbitBroker(broker), TestApp(app):
        handle.mock.assert_called_once_with({"name": "John", "user_id": 1})
        handle_response.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio
async def test_base_router_nats():
    from docs.docs_src.getting_started.routers.nats.router import (
        app,
        broker,
        handle,
        handle_response,
    )

    async with TestNatsBroker(broker), TestApp(app):
        handle.mock.assert_called_once_with({"name": "John", "user_id": 1})
        handle_response.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio
async def test_base_router_redis():
    from docs.docs_src.getting_started.routers.redis.router import (
        app,
        broker,
        handle,
        handle_response,
    )

    async with TestRedisBroker(broker), TestApp(app):
        handle.mock.assert_called_once_with({"name": "John", "user_id": 1})
        handle_response.mock.assert_called_once_with("Hi!")
