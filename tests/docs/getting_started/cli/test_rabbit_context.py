import pytest

from faststream import TestApp, context
from faststream.rabbit import TestRabbitBroker
from tests.marks import pydanticV2
from tests.mocks import mock_pydantic_settings_env


@pydanticV2
@pytest.mark.asyncio
async def test():
    with mock_pydantic_settings_env(
        {"host": "amqp://guest:guest@localhost:5673/"}  # pragma: allowlist secret
    ):
        from docs.docs_src.getting_started.cli.rabbit_context import app, broker

        async with TestRabbitBroker(broker):
            async with TestApp(app, {"env": ".env"}):
                assert (
                    context.get("settings").host
                    == "amqp://guest:guest@localhost:5673/"  # pragma: allowlist secret
                )
