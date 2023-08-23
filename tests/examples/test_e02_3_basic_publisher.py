import pytest

from examples.e02_3_basic_publisher import app, handle, handle_response
from propan import TestApp as T


@pytest.mark.asyncio
@pytest.mark.rabbit
async def test_example():
    async with T(app):
        await handle.wait_call(3)
        await handle_response.wait_call(3)

    handle.mock.assert_called_with("Hello!")
    handle_response.mock.assert_called_with("Response")
