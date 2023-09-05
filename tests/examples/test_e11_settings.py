import pytest

from examples.e11_settings import app, handle
from faststream import TestApp


@pytest.mark.asyncio
@pytest.mark.rabbit
async def test_example():
    async with TestApp(app):
        await handle.wait_call(3)

    handle.mock.assert_called_with("Hello!")
