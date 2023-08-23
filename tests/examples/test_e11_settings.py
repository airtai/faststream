import pytest

from examples.e11_settings import app, handle
from propan import TestApp as T


@pytest.mark.asyncio
@pytest.mark.rabbit
async def test_example():
    async with T(app):
        await handle.wait_call(3)

    handle.mock.assert_called_with("Hello!")
