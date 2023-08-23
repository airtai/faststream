import pytest

from examples.router.basic_consume import app, handle
from propan import TestApp as T


@pytest.mark.asyncio
@pytest.mark.kafka
async def test_example():
    async with T(app):
        await handle.wait_call(3)

    handle.mock.assert_called_with("Hello!")
