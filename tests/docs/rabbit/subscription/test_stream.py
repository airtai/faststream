import pytest

from faststream import TestApp


@pytest.mark.asyncio
@pytest.mark.rabbit
async def test_stream():
    from docs.docs_src.rabbit.subscription.stream import app, handle

    async with TestApp(app):
        await handle.wait_call(3)

        handle.mock.assert_called_with("Hi!")
