import pytest

from faststream import TestApp, context
from faststream.nats import TestNatsBroker
from tests.marks import pydanticV2
from tests.mocks import mock_pydantic_settings_env


@pydanticV2
@pytest.mark.asyncio
async def test():
    with mock_pydantic_settings_env({"host": "localhost"}):
        from docs.docs_src.getting_started.cli.nats_context import app, broker

        async with TestNatsBroker(broker):
            async with TestApp(app, {"env": ""}):
                assert context.get("settings").host == "localhost"
