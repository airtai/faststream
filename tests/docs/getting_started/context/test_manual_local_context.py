import pytest

from faststream.confluent import TestKafkaBroker as TestConfluentKafkaBroker
from faststream.kafka import TestKafkaBroker
from faststream.nats import TestNatsBroker
from faststream.rabbit import TestRabbitBroker
from faststream.redis import TestRedisBroker


@pytest.mark.asyncio()
async def test_manual_local_context_kafka():
    from docs.docs_src.getting_started.context.kafka.manual_local_context import (
        broker,
        handle,
    )

    async with TestKafkaBroker(broker) as br:
        await br.publish("Hi!", "test-topic")

        handle.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio()
async def test_manual_local_context_confluent():
    from docs.docs_src.getting_started.context.confluent.manual_local_context import (
        broker,
        handle,
    )

    async with TestConfluentKafkaBroker(broker) as br:
        await br.publish("Hi!", "test-topic")

        handle.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio()
async def test_manual_local_context_rabbit():
    from docs.docs_src.getting_started.context.rabbit.manual_local_context import (
        broker,
        handle,
    )

    async with TestRabbitBroker(broker) as br:
        await br.publish("Hi!", "test-queue")

        handle.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio()
async def test_manual_local_context_nats():
    from docs.docs_src.getting_started.context.nats.manual_local_context import (
        broker,
        handle,
    )

    async with TestNatsBroker(broker) as br:
        await br.publish("Hi!", "test-subject")

        handle.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio()
async def test_manual_local_context_redis():
    from docs.docs_src.getting_started.context.redis.manual_local_context import (
        broker,
        handle,
    )

    async with TestRedisBroker(broker) as br:
        await br.publish("Hi!", "test-channel")

        handle.mock.assert_called_once_with("Hi!")
