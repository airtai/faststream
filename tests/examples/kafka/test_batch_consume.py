import pytest

from examples.kafka.batch_consume import app, handle
from faststream import TestApp


@pytest.mark.asyncio
@pytest.mark.kafka
async def test_example():
    async with TestApp(app):
        await handle.wait_call(3)
    assert set(handle.mock.call_args[0][0]) == {"hi", "FastStream"}
