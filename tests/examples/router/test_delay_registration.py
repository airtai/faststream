import pytest

from examples.router.delay_registration import app, broker
from faststream.kafka import TestApp, TestKafkaBroker


@pytest.mark.asyncio()
async def test_example():
    handle = broker.handlers["prefix_in"].calls[0].handler

    async with TestKafkaBroker(broker), TestApp(app):
        await handle.wait_call(3)

        handle.mock.assert_called_with("Hello!")
