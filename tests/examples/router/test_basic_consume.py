import pytest

from examples.router.basic_consume import app, handle, broker
from faststream.kafka import TestApp, TestKafkaBroker


@pytest.mark.asyncio
async def test_example():
    async with TestKafkaBroker(broker, connect_only=True):
        async with TestApp(app):
            await handle.wait_call(3)

            handle.mock.assert_called_with("Hello!")
