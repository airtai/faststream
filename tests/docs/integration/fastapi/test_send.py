import pytest
from fastapi.testclient import TestClient

from faststream.confluent import TestKafkaBroker as TestConfluentKafkaBroker
from faststream.kafka import TestKafkaBroker
from faststream.nats import TestNatsBroker
from faststream.rabbit import TestRabbitBroker
from faststream.redis import TestRedisBroker


@pytest.mark.asyncio()
async def test_fastapi_kafka_send():
    from docs.docs_src.integrations.fastapi.kafka.send import app, router

    @router.subscriber("test")
    async def handler(): ...

    async with TestKafkaBroker(router.broker):
        with TestClient(app) as client:
            assert client.get("/").text == '"Hello, HTTP!"'

        handler.mock.assert_called_once_with("Hello, Kafka!")


@pytest.mark.asyncio()
async def test_fastapi_confluent_send():
    from docs.docs_src.integrations.fastapi.confluent.send import app, router

    @router.subscriber("test")
    async def handler(): ...

    async with TestConfluentKafkaBroker(router.broker):
        with TestClient(app) as client:
            assert client.get("/").text == '"Hello, HTTP!"'

        handler.mock.assert_called_once_with("Hello, Kafka!")


@pytest.mark.asyncio()
async def test_fastapi_rabbit_send():
    from docs.docs_src.integrations.fastapi.rabbit.send import app, router

    @router.subscriber("test")
    async def handler(): ...

    async with TestRabbitBroker(router.broker):
        with TestClient(app) as client:
            assert client.get("/").text == '"Hello, HTTP!"'

        handler.mock.assert_called_once_with("Hello, Rabbit!")


@pytest.mark.asyncio()
async def test_fastapi_nats_send():
    from docs.docs_src.integrations.fastapi.nats.send import app, router

    @router.subscriber("test")
    async def handler(): ...

    async with TestNatsBroker(router.broker):
        with TestClient(app) as client:
            assert client.get("/").text == '"Hello, HTTP!"'

        handler.mock.assert_called_once_with("Hello, NATS!")


@pytest.mark.asyncio()
async def test_fastapi_redis_send():
    from docs.docs_src.integrations.fastapi.redis.send import app, router

    @router.subscriber("test")
    async def handler(): ...

    async with TestRedisBroker(router.broker):
        with TestClient(app) as client:
            assert client.get("/").text == '"Hello, HTTP!"'

        handler.mock.assert_called_once_with("Hello, Redis!")
