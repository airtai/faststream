import pytest

from faststream import TestApp
from faststream.kafka import TestKafkaBroker
from faststream.rabbit import TestRabbitBroker
from faststream.nats import TestNatsBroker


@pytest.mark.asyncio
async def test_kafka_filtering():
    from docs.docs_src.getting_started.subscription.filter_kafka import (
        app,
        broker,
        default_handler,
        handle,
    )

    async with TestKafkaBroker(broker):
        async with TestApp(app):
            handle.mock.assert_called_once_with({"name": "John", "user_id": 1})
            default_handler.mock.assert_called_once_with("Hello, FastStream!")


@pytest.mark.asyncio
async def test_rabbit_filtering():
    from docs.docs_src.getting_started.subscription.filter_rabbit import (
        app,
        broker,
        default_handler,
        handle,
    )

    async with TestRabbitBroker(broker):
        async with TestApp(app):
            handle.mock.assert_called_once_with({"name": "John", "user_id": 1})
            default_handler.mock.assert_called_once_with("Hello, FastStream!")


@pytest.mark.asyncio
async def test_nats_filtering():
    from docs.docs_src.getting_started.subscription.filter_nats import (
        app,
        broker,
        default_handler,
        handle,
    )

    async with TestNatsBroker(broker):
        async with TestApp(app):
            handle.mock.assert_called_once_with({"name": "John", "user_id": 1})
            default_handler.mock.assert_called_once_with("Hello, FastStream!")
