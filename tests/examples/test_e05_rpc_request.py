import pytest

from examples.e05_rpc_request import app, handle
from faststream import TestApp as T


@pytest.mark.asyncio
@pytest.mark.rabbit
async def test_example():
    async with T(app):
        await handle.wait_call(3)

    handle.mock.assert_called_with("ping")
