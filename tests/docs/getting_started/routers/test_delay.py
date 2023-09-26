import pytest

from faststream import TestApp
from faststream.kafka import TestKafkaBroker
from faststream.rabbit import TestRabbitBroker
from faststream.nats import TestNatsBroker


@pytest.mark.asyncio
async def test_delay_router_kafka():
    from docs.docs_src.getting_started.routers.router_delay_kafka import (
        app,
        broker,
    )

    async with TestKafkaBroker(broker) as br:
        async with TestApp(app):
            list(br.handlers.values())[0].calls[0][0].mock.assert_called_once_with(
                {"name": "John", "user_id": 1}
            )


@pytest.mark.asyncio
async def test_delay_router_rabbit():
    from docs.docs_src.getting_started.routers.router_delay_rabbit import (
        app,
        broker,
    )

    async with TestRabbitBroker(broker) as br:
        async with TestApp(app):
            list(br.handlers.values())[0].calls[0][0].mock.assert_called_once_with(
                {"name": "John", "user_id": 1}
            )


@pytest.mark.asyncio
async def test_delay_router_nats():
    from docs.docs_src.getting_started.routers.router_delay_nats import (
        app,
        broker,
    )

    async with TestNatsBroker(broker) as br:
        async with TestApp(app):
            list(br.handlers.values())[0].calls[0][0].mock.assert_called_once_with(
                {"name": "John", "user_id": 1}
            )
