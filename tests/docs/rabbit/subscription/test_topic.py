import pytest

from faststream.rabbit import TestApp, TestRabbitBroker


@pytest.mark.asyncio
async def test_index():
    from docs.docs_src.rabbit.subscription.topic import (
        app,
        base_handler1,
        base_handler3,
        broker,
    )

    async with TestRabbitBroker(broker, connect_only=True):
        async with TestApp(app):
            assert base_handler1.mock.call_count == 3
            assert base_handler3.mock.call_count == 1
