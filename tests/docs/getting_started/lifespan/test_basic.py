import pytest

from faststream import TestApp, context
from faststream.kafka import TestKafkaBroker
from faststream.rabbit import TestRabbitBroker
from tests.marks import pydanticV2
from tests.mocks import mock_pydantic_settings_env


@pydanticV2
@pytest.mark.asyncio
async def test_rabbit_basic_lifespan():
    with mock_pydantic_settings_env({"host": "localhost"}):
        from docs.docs_src.getting_started.lifespan.rabbit.basic import app, broker

        async with TestRabbitBroker(broker):
            async with TestApp(app):
                assert context.get("settings").host == "localhost"


@pydanticV2
@pytest.mark.asyncio
async def test_kafka_basic_lifespan():
    with mock_pydantic_settings_env({"host": "localhost"}):
        from docs.docs_src.getting_started.lifespan.kafka.basic import app, broker

        async with TestKafkaBroker(broker):
            async with TestApp(app):
                assert context.get("settings").host == "localhost"
