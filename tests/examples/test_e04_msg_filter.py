import pytest

from examples.e04_msg_filter import app, handle_json, handle_other_messages
from propan import TestApp as T


@pytest.mark.asyncio
@pytest.mark.rabbit
async def test_example():
    async with T(app):
        await handle_json.wait_call(3)
        await handle_other_messages.wait_call(3)

    handle_json.mock.assert_called_with({"msg": "Hello!"})
    handle_other_messages.mock.assert_called_with("Hello!")
