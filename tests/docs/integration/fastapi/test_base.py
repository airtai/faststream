import pytest
from fastapi.testclient import TestClient

from faststream.kafka import TestKafkaBroker
from faststream.nats import TestNatsBroker
from faststream.rabbit import TestRabbitBroker
from faststream.redis import TestRedisBroker


@pytest.mark.asyncio()
async def test_fastapi_kafka_base():
    from docs.docs_src.integrations.fastapi.kafka.base import app, hello, router

    async with TestKafkaBroker(router.broker) as br:
        with TestClient(app) as client:
            assert client.get("/").text == '"Hello, HTTP!"'

        await br.publish({"m": {}}, "test")

        hello.mock.assert_called_once_with({"m": {}})

        list(br._publishers.values())[0].mock.assert_called_with(  # noqa: RUF015
            {"response": "Hello, Kafka!"}
        )


@pytest.mark.asyncio()
async def test_fastapi_rabbit_base():
    from docs.docs_src.integrations.fastapi.rabbit.base import app, hello, router

    async with TestRabbitBroker(router.broker) as br:
        with TestClient(app) as client:
            assert client.get("/").text == '"Hello, HTTP!"'

        await br.publish({"m": {}}, "test")

        hello.mock.assert_called_once_with({"m": {}})

        list(br._publishers.values())[0].mock.assert_called_with(  # noqa: RUF015
            {"response": "Hello, Rabbit!"}
        )


@pytest.mark.asyncio()
async def test_fastapi_nats_base():
    from docs.docs_src.integrations.fastapi.nats.base import app, hello, router

    async with TestNatsBroker(router.broker) as br:
        with TestClient(app) as client:
            assert client.get("/").text == '"Hello, HTTP!"'

        await br.publish({"m": {}}, "test")

        hello.mock.assert_called_once_with({"m": {}})

        list(br._publishers.values())[0].mock.assert_called_with(  # noqa: RUF015
            {"response": "Hello, NATS!"}
        )


@pytest.mark.asyncio()
async def test_fastapi_redis_base():
    from docs.docs_src.integrations.fastapi.redis.base import app, hello, router

    async with TestRedisBroker(router.broker) as br:
        with TestClient(app) as client:
            assert client.get("/").text == '"Hello, HTTP!"'

        await br.publish({"m": {}}, "test")

        hello.mock.assert_called_once_with({"m": {}})

        list(br._publishers.values())[0].mock.assert_called_with(  # noqa: RUF015
            {"response": "Hello, Redis!"}
        )
