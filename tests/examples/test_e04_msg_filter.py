import pytest

from examples.e04_msg_filter import app, handle_json, handle_other_messages
from faststream import TestApp


@pytest.mark.asyncio
@pytest.mark.rabbit
async def test_example():
    async with TestApp(app):
        await handle_json.wait_call(3)
        await handle_other_messages.wait_call(3)

    handle_json.mock.assert_called_with({"msg": "Hello!"})
    handle_other_messages.mock.assert_called_with("Hello!")
