import pytest

from faststream.kafka import TestKafkaBroker
from faststream.nats import TestNatsBroker
from faststream.rabbit import TestRabbitBroker


@pytest.mark.asyncio
async def test_cast_kafka():
    from docs.docs_src.getting_started.context.cast_kafka import (
        broker,
        handle,
        handle_int,
    )

    async with TestKafkaBroker(broker) as br:
        await br.publish("Hi!", "test-topic")

        handle.mock.assert_called_once_with("Hi!")

        await br.publish("Hi!", "test-topic2")

        handle_int.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio
async def test_cast_rabbit():
    from docs.docs_src.getting_started.context.cast_rabbit import (
        broker,
        handle,
        handle_int,
    )

    async with TestRabbitBroker(broker) as br:
        await br.publish("Hi!", "test-queue")

        handle.mock.assert_called_once_with("Hi!")

        await br.publish("Hi!", "test-queue2")

        handle_int.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio
async def test_cast_nats():
    from docs.docs_src.getting_started.context.cast_nats import (
        broker,
        handle,
        handle_int,
    )

    async with TestNatsBroker(broker) as br:
        await br.publish("Hi!", "test-subject")

        handle.mock.assert_called_once_with("Hi!")

        await br.publish("Hi!", "test-subject2")

        handle_int.mock.assert_called_once_with("Hi!")
