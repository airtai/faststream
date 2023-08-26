import pytest

from examples.router.basic_publish import app, handle, handle_response
from faststream import TestApp as T


@pytest.mark.asyncio
@pytest.mark.kafka
async def test_example():
    async with T(app):
        await handle.wait_call(3)
        await handle_response.wait_call(3)

    handle.mock.assert_called_with("Hello!")
    handle_response.mock.assert_called_with("Response")
