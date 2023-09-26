import pytest
from fastapi.testclient import TestClient

from faststream.kafka import TestKafkaBroker
from faststream.nats import TestNatsBroker
from faststream.rabbit import TestRabbitBroker


@pytest.mark.asyncio
async def test_fastapi_kafka_depends():
    from docs.docs_src.integrations.fastapi.depends_kafka import app, router

    @router.subscriber("test")
    async def handler():
        ...

    async with TestKafkaBroker(router.broker):
        with TestClient(app) as client:
            assert client.get("/").text == '"Hello, HTTP!"'

        handler.mock.assert_called_once_with("Hello, Kafka!")


@pytest.mark.asyncio
async def test_fastapi_rabbit_depends():
    from docs.docs_src.integrations.fastapi.depends_rabbit import app, router

    @router.subscriber("test")
    async def handler():
        ...

    async with TestRabbitBroker(router.broker):
        with TestClient(app) as client:
            assert client.get("/").text == '"Hello, HTTP!"'

        handler.mock.assert_called_once_with("Hello, Rabbit!")


@pytest.mark.asyncio
async def test_fastapi_nats_depends():
    from docs.docs_src.integrations.fastapi.depends_nats import app, router

    @router.subscriber("test")
    async def handler():
        ...

    async with TestNatsBroker(router.broker):
        with TestClient(app) as client:
            assert client.get("/").text == '"Hello, HTTP!"'

        handler.mock.assert_called_once_with("Hello, NATS!")
