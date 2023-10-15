import pytest

from faststream.kafka import TestKafkaBroker
from faststream.nats import TestNatsBroker
from faststream.rabbit import TestRabbitBroker


@pytest.mark.asyncio
async def test_fields_access_kafka():
    from docs.docs_src.getting_started.context.fields_access_kafka import (
        broker,
        handle,
    )

    async with TestKafkaBroker(broker) as br:
        await br.publish("Hi!", "test-topic", headers={"user": "John"})

        handle.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio
async def test_fields_access_rabbit():
    from docs.docs_src.getting_started.context.fields_access_rabbit import (
        broker,
        handle,
    )

    async with TestRabbitBroker(broker) as br:
        await br.publish("Hi!", "test-queue", headers={"user": "John"})

        handle.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio
async def test_fields_access_nats():
    from docs.docs_src.getting_started.context.fields_access_nats import (
        broker,
        handle,
    )

    async with TestNatsBroker(broker) as br:
        await br.publish("Hi!", "test-subject", headers={"user": "John"})

        handle.mock.assert_called_once_with("Hi!")
