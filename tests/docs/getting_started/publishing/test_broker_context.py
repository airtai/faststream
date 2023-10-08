import pytest

from faststream import TestApp
from faststream.kafka import TestKafkaBroker
from faststream.nats import TestNatsBroker
from faststream.rabbit import TestRabbitBroker


@pytest.mark.asyncio
@pytest.mark.kafka
async def test_broker_context_kafka():
    from docs.docs_src.getting_started.publishing.broker_context_kafka import (
        app,
        broker,
        handle,
    )

    async with TestKafkaBroker(broker, connect_only=True, with_real=True):
        async with TestApp(app):
            await handle.wait_call(3)
            handle.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio
@pytest.mark.nats
async def test_broker_context_nats():
    from docs.docs_src.getting_started.publishing.broker_context_nats import (
        app,
        broker,
        handle,
    )

    async with TestNatsBroker(broker, connect_only=True, with_real=True):
        async with TestApp(app):
            await handle.wait_call(3)
            handle.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio
@pytest.mark.rabbit
async def test_broker_context_rabbit():
    from docs.docs_src.getting_started.publishing.broker_context_rabbit import (
        app,
        broker,
        handle,
    )

    async with TestRabbitBroker(broker, connect_only=True, with_real=True):
        async with TestApp(app):
            await handle.wait_call(3)
            handle.mock.assert_called_once_with("Hi!")
