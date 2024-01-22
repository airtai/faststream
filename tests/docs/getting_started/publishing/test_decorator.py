import pytest

from faststream import TestApp
from faststream.confluent import TestKafkaBroker as TestConfluentKafkaBroker
from faststream.kafka import TestKafkaBroker
from faststream.nats import TestNatsBroker
from faststream.rabbit import TestRabbitBroker
from faststream.redis import TestRedisBroker


@pytest.mark.asyncio()
async def test_decorator_kafka():
    from docs.docs_src.getting_started.publishing.kafka.decorator import (
        app,
        broker,
        handle,
        handle_next,
    )

    async with TestKafkaBroker(broker), TestApp(app):
        handle.mock.assert_called_once_with("")
        handle_next.mock.assert_called_once_with("Hi!")
        next(iter(broker._publishers.values())).mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio()
async def test_decorator_confluent():
    from docs.docs_src.getting_started.publishing.confluent.decorator import (
        app,
        broker,
        handle,
        handle_next,
    )

    async with TestConfluentKafkaBroker(broker), TestApp(app):
        handle.mock.assert_called_once_with("")
        handle_next.mock.assert_called_once_with("Hi!")
        next(iter(broker._publishers.values())).mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio()
async def test_decorator_rabbit():
    from docs.docs_src.getting_started.publishing.rabbit.decorator import (
        app,
        broker,
        handle,
        handle_next,
    )

    async with TestRabbitBroker(broker), TestApp(app):
        handle.mock.assert_called_once_with("")
        handle_next.mock.assert_called_once_with("Hi!")
        next(iter(broker._publishers.values())).mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio()
async def test_decorator_nats():
    from docs.docs_src.getting_started.publishing.nats.decorator import (
        app,
        broker,
        handle,
        handle_next,
    )

    async with TestNatsBroker(broker), TestApp(app):
        handle.mock.assert_called_once_with("")
        handle_next.mock.assert_called_once_with("Hi!")
        next(iter(broker._publishers.values())).mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio()
async def test_decorator_redis():
    from docs.docs_src.getting_started.publishing.redis.decorator import (
        app,
        broker,
        handle,
        handle_next,
    )

    async with TestRedisBroker(broker), TestApp(app):
        handle.mock.assert_called_once_with("")
        handle_next.mock.assert_called_once_with("Hi!")
        next(iter(broker._publishers.values())).mock.assert_called_once_with("Hi!")
