import pytest

from faststream import TestApp
from faststream.kafka import TestKafkaBroker
from faststream.nats import TestNatsBroker
from faststream.rabbit import TestRabbitBroker


@pytest.mark.asyncio
async def test_broker_kafka():
    from docs.docs_src.getting_started.publishing.broker_kafka import (
        app,
        broker,
        handle,
        handle_next,
    )

    async with TestKafkaBroker(broker, connect_only=True):
        async with TestApp(app):
            handle.mock.assert_called_once_with("")
            handle_next.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio
async def test_broker_rabbit():
    from docs.docs_src.getting_started.publishing.broker_rabbit import (
        app,
        broker,
        handle,
        handle_next,
    )

    async with TestRabbitBroker(broker, connect_only=True):
        async with TestApp(app):
            handle.mock.assert_called_once_with("")
            handle_next.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio
async def test_broker_nats():
    from docs.docs_src.getting_started.publishing.broker_nats import (
        app,
        broker,
        handle,
        handle_next,
    )

    async with TestNatsBroker(broker, connect_only=True):
        async with TestApp(app):
            handle.mock.assert_called_once_with("")
            handle_next.mock.assert_called_once_with("Hi!")
