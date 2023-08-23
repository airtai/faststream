import pytest

from examples.router.delay_registration import app, broker
from propan import TestApp as T


@pytest.mark.asyncio
@pytest.mark.kafka
async def test_example():
    handle = broker.handlers["prefix_in"].calls[0][0]

    async with T(app):
        await handle.wait_call(3)

    handle.mock.assert_called_with("Hello!")
