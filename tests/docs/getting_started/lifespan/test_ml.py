import pytest

from faststream import TestApp
from faststream.kafka import TestKafkaBroker
from faststream.nats import TestNatsBroker
from faststream.rabbit import TestRabbitBroker


@pytest.mark.asyncio
async def test_rabbit_ml_lifespan():
    from docs.docs_src.getting_started.lifespan.rabbit.ml import app, broker, predict

    async with TestRabbitBroker(broker):
        async with TestApp(app):
            assert {"result": 42.0} == await broker.publish(1.0, "test", rpc=True)

            predict.mock.assert_called_once_with(1.0)


@pytest.mark.asyncio
async def test_kafka_ml_lifespan():
    from docs.docs_src.getting_started.lifespan.kafka.ml import app, broker, predict

    async with TestKafkaBroker(broker):
        async with TestApp(app):
            assert {"result": 42.0} == await broker.publish(1.0, "test", rpc=True)

            predict.mock.assert_called_once_with(1.0)


@pytest.mark.asyncio
async def test_nats_ml_lifespan():
    from docs.docs_src.getting_started.lifespan.nats.ml import app, broker, predict

    async with TestNatsBroker(broker):
        async with TestApp(app):
            assert {"result": 42.0} == await broker.publish(1.0, "test", rpc=True)

            predict.mock.assert_called_once_with(1.0)
