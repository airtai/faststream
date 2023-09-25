import pytest

from faststream import TestApp
from faststream.kafka import TestKafkaBroker
from faststream.rabbit import TestRabbitBroker


@pytest.mark.asyncio
async def test_base_router_kafka():
    from docs.docs_src.getting_started.routers.router_kafka import (
        app,
        broker,
        handle,
        handle_response,
    )

    async with TestKafkaBroker(broker):
        async with TestApp(app):
            handle.mock.assert_called_once_with({"name": "John", "user_id": 1})
            handle_response.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio
async def test_base_router_rabbit():
    from docs.docs_src.getting_started.routers.router_rabbit import (
        app,
        broker,
        handle,
        handle_response,
    )

    async with TestRabbitBroker(broker):
        async with TestApp(app):
            handle.mock.assert_called_once_with({"name": "John", "user_id": 1})
            handle_response.mock.assert_called_once_with("Hi!")
