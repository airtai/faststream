import pytest

from faststream import TestApp
from faststream.confluent import TestKafkaBroker as TestConfluentKafkaBroker
from faststream.kafka import TestKafkaBroker
from faststream.nats import TestNatsBroker
from faststream.rabbit import TestRabbitBroker
from faststream.redis import TestRedisBroker


@pytest.mark.asyncio()
@pytest.mark.kafka()
async def test_broker_context_kafka():
    from docs.docs_src.getting_started.publishing.kafka.broker_context import (
        app,
        broker,
        handle,
    )

    async with TestKafkaBroker(broker, with_real=True), TestApp(app):
        await handle.wait_call(3)
        handle.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio()
@pytest.mark.kafka()
async def test_broker_context_confluent():
    from docs.docs_src.getting_started.publishing.confluent.broker_context import (
        app,
        broker,
        handle,
    )

    async with TestConfluentKafkaBroker(broker, with_real=True), TestApp(app):
        await handle.wait_call(5)
        handle.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio()
@pytest.mark.nats()
async def test_broker_context_nats():
    from docs.docs_src.getting_started.publishing.nats.broker_context import (
        app,
        broker,
        handle,
    )

    async with TestNatsBroker(broker, with_real=True), TestApp(app):
        await handle.wait_call(3)
        handle.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio()
@pytest.mark.rabbit()
async def test_broker_context_rabbit():
    from docs.docs_src.getting_started.publishing.rabbit.broker_context import (
        app,
        broker,
        handle,
    )

    async with TestRabbitBroker(broker, with_real=True), TestApp(app):
        await handle.wait_call(3)
        handle.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio()
@pytest.mark.redis()
async def test_broker_context_redis():
    from docs.docs_src.getting_started.publishing.redis.broker_context import (
        app,
        broker,
        handle,
    )

    async with TestRedisBroker(broker, with_real=True), TestApp(app):
        await handle.wait_call(3)
        handle.mock.assert_called_once_with("Hi!")
