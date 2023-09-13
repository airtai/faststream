import pytest

from examples.router.delay_registration import app, broker
from faststream import TestApp


@pytest.mark.asyncio
@pytest.mark.kafka
async def test_example():
    handle = broker.handlers["prefix_in"].calls[0][0]

    async with TestApp(app):
        await handle.wait_call(3)

    handle.mock.assert_called_with("Hello!")
