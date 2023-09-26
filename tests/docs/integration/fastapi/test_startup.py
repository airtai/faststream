import pytest
from fastapi.testclient import TestClient

from faststream.kafka import TestKafkaBroker
from faststream.nats import TestNatsBroker
from faststream.rabbit import TestRabbitBroker


@pytest.mark.asyncio
async def test_fastapi_kafka_startup():
    from docs.docs_src.integrations.fastapi.startup_kafka import app, hello, router

    @router.subscriber("test")
    async def handler():
        ...

    async with TestKafkaBroker(router.broker):
        with TestClient(app):
            hello.mock.assert_called_once_with("Hello!")


@pytest.mark.asyncio
async def test_fastapi_rabbit_startup():
    from docs.docs_src.integrations.fastapi.startup_rabbit import app, hello, router

    @router.subscriber("test")
    async def handler():
        ...

    async with TestRabbitBroker(router.broker):
        with TestClient(app):
            hello.mock.assert_called_once_with("Hello!")


@pytest.mark.asyncio
async def test_fastapi_nats_startup():
    from docs.docs_src.integrations.fastapi.startup_nats import app, hello, router

    @router.subscriber("test")
    async def handler():
        ...

    async with TestNatsBroker(router.broker):
        with TestClient(app):
            hello.mock.assert_called_once_with("Hello!")
