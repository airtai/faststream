import pytest

from faststream.confluent import TestKafkaBroker as TestConfluentKafkaBroker
from faststream.kafka import TestKafkaBroker
from faststream.nats import TestNatsBroker
from faststream.rabbit import TestRabbitBroker
from faststream.redis import TestRedisBroker


@pytest.mark.asyncio()
async def test_cast_kafka():
    from docs.docs_src.getting_started.context.kafka.cast import (
        broker,
        handle,
        handle_int,
    )

    async with TestKafkaBroker(broker) as br:
        await br.publish("Hi!", "test-topic")

        handle.mock.assert_called_once_with("Hi!")

        await br.publish("Hi!", "test-topic2")

        handle_int.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio()
async def test_cast_confluent():
    from docs.docs_src.getting_started.context.confluent.cast import (
        broker,
        handle,
        handle_int,
    )

    async with TestConfluentKafkaBroker(broker) as br:
        await br.publish("Hi!", "test-topic")

        handle.mock.assert_called_once_with("Hi!")

        await br.publish("Hi!", "test-topic2")

        handle_int.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio()
async def test_cast_rabbit():
    from docs.docs_src.getting_started.context.rabbit.cast import (
        broker,
        handle,
        handle_int,
    )

    async with TestRabbitBroker(broker) as br:
        await br.publish("Hi!", "test-queue")

        handle.mock.assert_called_once_with("Hi!")

        await br.publish("Hi!", "test-queue2")

        handle_int.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio()
async def test_cast_nats():
    from docs.docs_src.getting_started.context.nats.cast import (
        broker,
        handle,
        handle_int,
    )

    async with TestNatsBroker(broker) as br:
        await br.publish("Hi!", "test-subject")

        handle.mock.assert_called_once_with("Hi!")

        await br.publish("Hi!", "test-subject2")

        handle_int.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio()
async def test_cast_redis():
    from docs.docs_src.getting_started.context.redis.cast import (
        broker,
        handle,
        handle_int,
    )

    async with TestRedisBroker(broker) as br:
        await br.publish("Hi!", "test-channel")

        handle.mock.assert_called_once_with("Hi!")

        await br.publish("Hi!", "test-channel2")

        handle_int.mock.assert_called_once_with("Hi!")
