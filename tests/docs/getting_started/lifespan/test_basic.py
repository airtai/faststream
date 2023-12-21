import pytest

from faststream import TestApp, context
from faststream.kafka import TestKafkaBroker
from faststream.nats import TestNatsBroker
from faststream.rabbit import TestRabbitBroker
from faststream.redis import TestRedisBroker
from tests.marks import pydanticV2
from tests.mocks import mock_pydantic_settings_env


@pydanticV2
@pytest.mark.asyncio()
async def test_rabbit_basic_lifespan():
    with mock_pydantic_settings_env({"host": "localhost"}):
        from docs.docs_src.getting_started.lifespan.rabbit.basic import app, broker

        async with TestRabbitBroker(broker), TestApp(app):
            assert context.get("settings").host == "localhost"


@pydanticV2
@pytest.mark.asyncio()
async def test_kafka_basic_lifespan():
    with mock_pydantic_settings_env({"host": "localhost"}):
        from docs.docs_src.getting_started.lifespan.kafka.basic import app, broker

        async with TestKafkaBroker(broker), TestApp(app):
            assert context.get("settings").host == "localhost"


@pydanticV2
@pytest.mark.asyncio()
async def test_nats_basic_lifespan():
    with mock_pydantic_settings_env({"host": "localhost"}):
        from docs.docs_src.getting_started.lifespan.nats.basic import app, broker

        async with TestNatsBroker(broker), TestApp(app):
            assert context.get("settings").host == "localhost"


@pydanticV2
@pytest.mark.asyncio()
async def test_redis_basic_lifespan():
    with mock_pydantic_settings_env({"host": "localhost"}):
        from docs.docs_src.getting_started.lifespan.redis.basic import app, broker

        async with TestRedisBroker(broker), TestApp(app):
            assert context.get("settings").host == "localhost"
