import pytest

from faststream import TestApp
from faststream.kafka import TestKafkaBroker
from faststream.nats import TestNatsBroker
from faststream.rabbit import TestRabbitBroker


@pytest.mark.asyncio
async def test_decorator_kafka():
    from docs.docs_src.getting_started.publishing.decorator_kafka import (
        app,
        broker,
        handle,
        handle_next,
    )

    async with TestKafkaBroker(broker, connect_only=True):
        async with TestApp(app):
            handle.mock.assert_called_once_with("")
            handle_next.mock.assert_called_once_with("Hi!")
            list(broker._publishers.values())[0].mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio
async def test_decorator_rabbit():
    from docs.docs_src.getting_started.publishing.decorator_rabbit import (
        app,
        broker,
        handle,
        handle_next,
    )

    async with TestRabbitBroker(broker, connect_only=True):
        async with TestApp(app):
            handle.mock.assert_called_once_with("")
            handle_next.mock.assert_called_once_with("Hi!")
            list(broker._publishers.values())[0].mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio
async def test_decorator_nats():
    from docs.docs_src.getting_started.publishing.decorator_nats import (
        app,
        broker,
        handle,
        handle_next,
    )

    async with TestNatsBroker(broker, connect_only=True):
        async with TestApp(app):
            handle.mock.assert_called_once_with("")
            handle_next.mock.assert_called_once_with("Hi!")
            list(broker._publishers.values())[0].mock.assert_called_once_with("Hi!")
