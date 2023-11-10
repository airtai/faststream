import pytest

from examples.e02_1_basic_publisher import app, broker, handle, handle_response
from faststream.rabbit import TestApp, TestRabbitBroker


@pytest.mark.asyncio
async def test_example():
    async with TestRabbitBroker(broker, connect_only=True):
        async with TestApp(app):
            await handle.wait_call(3)
            await handle_response.wait_call(3)

            handle.mock.assert_called_with("Hello!")
            handle_response.mock.assert_called_with("Response")
