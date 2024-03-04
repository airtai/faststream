import pytest
from fastapi.testclient import TestClient

from faststream.confluent import TestKafkaBroker as TestConfluentKafkaBroker
from faststream.kafka import TestKafkaBroker
from faststream.nats import TestNatsBroker
from faststream.rabbit import TestRabbitBroker
from faststream.redis import TestRedisBroker


@pytest.mark.asyncio()
async def test_fastapi_kafka_startup():
    from docs.docs_src.integrations.fastapi.kafka.startup import app, hello, router

    @router.subscriber("test")
    async def handler(): ...

    async with TestKafkaBroker(router.broker):
        with TestClient(app):
            hello.mock.assert_called_once_with("Hello!")


@pytest.mark.asyncio()
async def test_fastapi_confluent_startup():
    from docs.docs_src.integrations.fastapi.confluent.startup import app, hello, router

    @router.subscriber("test")
    async def handler(): ...

    async with TestConfluentKafkaBroker(router.broker):
        with TestClient(app):
            hello.mock.assert_called_once_with("Hello!")


@pytest.mark.asyncio()
async def test_fastapi_rabbit_startup():
    from docs.docs_src.integrations.fastapi.rabbit.startup import app, hello, router

    @router.subscriber("test")
    async def handler(): ...

    async with TestRabbitBroker(router.broker):
        with TestClient(app):
            hello.mock.assert_called_once_with("Hello!")


@pytest.mark.asyncio()
async def test_fastapi_nats_startup():
    from docs.docs_src.integrations.fastapi.nats.startup import app, hello, router

    @router.subscriber("test")
    async def handler(): ...

    async with TestNatsBroker(router.broker):
        with TestClient(app):
            hello.mock.assert_called_once_with("Hello!")


@pytest.mark.asyncio()
async def test_fastapi_redis_startup():
    from docs.docs_src.integrations.fastapi.redis.startup import app, hello, router

    @router.subscriber("test")
    async def handler(): ...

    async with TestRedisBroker(router.broker):
        with TestClient(app):
            hello.mock.assert_called_once_with("Hello!")
