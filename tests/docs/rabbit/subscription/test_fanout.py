import pytest

from faststream.rabbit import TestApp


@pytest.mark.asyncio
@pytest.mark.rabbit
async def test_index():
    from docs.docs_src.rabbit.subscription.fanout import (
        app,
        base_handler1,
        base_handler3,
    )

    async with TestApp(app):
        await base_handler1.wait_call(3)
        await base_handler3.wait_call(3)

        base_handler1.mock.assert_called_with("")
        base_handler3.mock.assert_called_with("")
