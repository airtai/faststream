import pytest

from faststream import TestApp
from faststream.kafka import TestKafkaBroker
from faststream.nats import TestNatsBroker
from faststream.rabbit import TestRabbitBroker


@pytest.mark.asyncio
async def test_parser_nats():
    from docs.docs_src.getting_started.serialization.parser_nats import (
        app,
        broker,
        handle,
    )

    async with TestNatsBroker(broker, connect_only=True):
        async with TestApp(app):
            handle.mock.assert_called_once_with("")


@pytest.mark.asyncio
async def test_parser_kafka():
    from docs.docs_src.getting_started.serialization.parser_kafka import (
        app,
        broker,
        handle,
    )

    async with TestKafkaBroker(broker, connect_only=True):
        async with TestApp(app):
            handle.mock.assert_called_once_with("")


@pytest.mark.asyncio
async def test_parser_rabbit():
    from docs.docs_src.getting_started.serialization.parser_rabbit import (
        app,
        broker,
        handle,
    )

    async with TestRabbitBroker(broker, connect_only=True):
        async with TestApp(app):
            handle.mock.assert_called_once_with("")
