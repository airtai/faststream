import pytest

from faststream.kafka import TestKafkaBroker
from faststream.nats import TestNatsBroker
from faststream.rabbit import TestRabbitBroker


@pytest.mark.asyncio
async def test_manual_local_context_kafka():
    from docs.docs_src.getting_started.context.manual_local_context_kafka import (
        broker,
        handle,
    )

    async with TestKafkaBroker(broker) as br:
        await br.publish("Hi!", "test-topic")

        handle.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio
async def test_manual_local_context_rabbit():
    from docs.docs_src.getting_started.context.manual_local_context_rabbit import (
        broker,
        handle,
    )

    async with TestRabbitBroker(broker) as br:
        await br.publish("Hi!", "test-queue")

        handle.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio
async def test_manual_local_context_nats():
    from docs.docs_src.getting_started.context.manual_local_context_nats import (
        broker,
        handle,
    )

    async with TestNatsBroker(broker) as br:
        await br.publish("Hi!", "test-subject")

        handle.mock.assert_called_once_with("Hi!")
