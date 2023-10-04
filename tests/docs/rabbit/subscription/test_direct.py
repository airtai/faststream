import pytest

from faststream.rabbit import TestApp, TestRabbitBroker


@pytest.mark.asyncio
async def test_index():
    from docs.docs_src.rabbit.subscription.direct import (
        app,
        base_handler1,
        base_handler3,
        broker,
    )

    async with TestRabbitBroker(broker, connect_only=True):
        async with TestApp(app):
            base_handler1.mock.assert_called_with("")
            base_handler3.mock.assert_called_once_with("")
