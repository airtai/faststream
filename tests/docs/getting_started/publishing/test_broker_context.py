import pytest

from faststream import TestApp


@pytest.mark.asyncio
@pytest.mark.kafka
async def test_broker_context_kafka():
    from docs.docs_src.getting_started.publishing.broker_context_kafka import (
        app,
        handle,
    )

    async with TestApp(app):
        await handle.wait_call(3)
        handle.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio
@pytest.mark.nats
async def test_broker_context_nats():
    from docs.docs_src.getting_started.publishing.broker_context_nats import app, handle

    async with TestApp(app):
        await handle.wait_call(3)
        handle.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio
@pytest.mark.rabbit
async def test_broker_context_rabbit():
    from docs.docs_src.getting_started.publishing.broker_context_rabbit import (
        app,
        handle,
    )

    async with TestApp(app):
        await handle.wait_call(3)
        handle.mock.assert_called_once_with("Hi!")
