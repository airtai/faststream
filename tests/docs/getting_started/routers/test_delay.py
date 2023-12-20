import pytest

from faststream import TestApp
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
        list(br.handlers.values())[0].calls[0][0].mock.assert_called_once_with(  # noqa: RUF015
            {"name": "John", "user_id": 1}
        )


@pytest.mark.asyncio()
async def test_delay_router_rabbit():
    from docs.docs_src.getting_started.routers.rabbit.router_delay import (
        app,
        broker,
    )

    async with TestRabbitBroker(broker) as br, TestApp(app):
        list(br.handlers.values())[0].calls[0][0].mock.assert_called_once_with(  # noqa: RUF015
            {"name": "John", "user_id": 1}
        )


@pytest.mark.asyncio()
async def test_delay_router_nats():
    from docs.docs_src.getting_started.routers.nats.router_delay import (
        app,
        broker,
    )

    async with TestNatsBroker(broker) as br, TestApp(app):
        list(br.handlers.values())[0].calls[0][0].mock.assert_called_once_with(  # noqa: RUF015
            {"name": "John", "user_id": 1}
        )


@pytest.mark.asyncio()
async def test_delay_router_redis():
    from docs.docs_src.getting_started.routers.redis.router_delay import (
        app,
        broker,
    )

    async with TestRedisBroker(broker) as br, TestApp(app):
        list(br.handlers.values())[0].calls[0][0].mock.assert_called_once_with(  # noqa: RUF015
            {"name": "John", "user_id": 1}
        )
