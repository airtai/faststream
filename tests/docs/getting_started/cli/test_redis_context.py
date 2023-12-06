import pytest

from faststream import TestApp, context
from faststream.redis import TestRedisBroker
from tests.marks import pydanticV2
from tests.mocks import mock_pydantic_settings_env


@pydanticV2
@pytest.mark.asyncio
async def test():
    with mock_pydantic_settings_env({"host": "redis://localhost:6380"}):
        from docs.docs_src.getting_started.cli.redis_context import app, broker

        async with TestRedisBroker(broker), TestApp(app, {"env": ".env"}):
            assert context.get("settings").host == "redis://localhost:6380"
