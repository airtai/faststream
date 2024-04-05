import pytest

from faststream import TestApp
from faststream.confluent import TestKafkaBroker as TestConfluentKafkaBroker
from faststream.kafka import TestKafkaBroker
from faststream.nats import TestNatsBroker
from faststream.rabbit import TestRabbitBroker
from faststream.redis import TestRedisBroker


@pytest.mark.asyncio()
async def test_delay_router_kafka():
    from docs.docs_src.getting_started.routers.kafka.router_delay import (
        app,
        broker,
    )

    async with TestKafkaBroker(broker) as br, TestApp(app):
        next(iter(br._subscribers.values())).calls[0].handler.mock.assert_called_once_with(
            {"name": "John", "user_id": 1}
        )


@pytest.mark.asyncio()
async def test_delay_router_confluent():
    from docs.docs_src.getting_started.routers.confluent.router_delay import (
        app,
        broker,
    )

    async with TestConfluentKafkaBroker(broker) as br, TestApp(app):
        next(iter(br._subscribers.values())).calls[0].handler.mock.assert_called_once_with(
            {"name": "John", "user_id": 1}
        )


@pytest.mark.asyncio()
async def test_delay_router_rabbit():
    from docs.docs_src.getting_started.routers.rabbit.router_delay import (
        app,
        broker,
    )

    async with TestRabbitBroker(broker) as br, TestApp(app):
        next(iter(br._subscribers.values())).calls[0].handler.mock.assert_called_once_with(
            {"name": "John", "user_id": 1}
        )


@pytest.mark.asyncio()
async def test_delay_router_nats():
    from docs.docs_src.getting_started.routers.nats.router_delay import (
        app,
        broker,
    )

    async with TestNatsBroker(broker) as br, TestApp(app):
        next(iter(br._subscribers.values())).calls[0].handler.mock.assert_called_once_with(
            {"name": "John", "user_id": 1}
        )


@pytest.mark.asyncio()
async def test_delay_router_redis():
    from docs.docs_src.getting_started.routers.redis.router_delay import (
        app,
        broker,
    )

    async with TestRedisBroker(broker) as br, TestApp(app):
        next(iter(br._subscribers.values())).calls[0].handler.mock.assert_called_once_with(
            {"name": "John", "user_id": 1}
        )
