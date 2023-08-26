import pytest

from examples.e01_basic_consume import app, handle
from faststream import TestApp as T


@pytest.mark.rabbit
@pytest.mark.asyncio
async def test_example():
    async with T(app):
        await handle.wait_call(3)

    handle.mock.assert_called_with("Hello!")
