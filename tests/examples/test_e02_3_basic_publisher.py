import pytest

from examples.e02_3_basic_publisher import app, handle, handle_response
from faststream import TestApp


@pytest.mark.asyncio
@pytest.mark.rabbit
async def test_example():
    async with TestApp(app):
        await handle.wait_call(3)
        await handle_response.wait_call(3)

    handle.mock.assert_called_with("Hello!")
    handle_response.mock.assert_called_with("Response")
