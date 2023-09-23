import pytest

from faststream import TestApp, context

from docs.docs_src.getting_started.cli.rabbit_context import app



@pytest.mark.asyncio
async def test():
    async with TestApp(app, { "env": "" }):
        assert context.get("settings").host == "amqp://guest:guest@localhost:5672/"
