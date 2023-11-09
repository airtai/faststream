import pytest

from faststream import TestApp
from faststream.kafka import TestKafkaBroker
from faststream.nats import TestNatsBroker
from faststream.rabbit import TestRabbitBroker


@pytest.mark.asyncio
async def test_custom_global_context_kafka():
    from docs.docs_src.getting_started.context.custom_global_context_kafka import (
        app,
        broker,
        handle,
    )

    async with TestKafkaBroker(broker) as br, TestApp(app):
        await br.publish("Hi!", "test-topic")

        handle.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio
async def test_custom_global_context_rabbit():
    from docs.docs_src.getting_started.context.custom_global_context_rabbit import (
        app,
        broker,
        handle,
    )

    async with TestRabbitBroker(broker) as br, TestApp(app):
        await br.publish("Hi!", "test-queue")

        handle.mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio
async def test_custom_global_context_nats():
    from docs.docs_src.getting_started.context.custom_global_context_nats import (
        app,
        broker,
        handle,
    )

    async with TestNatsBroker(broker) as br, TestApp(app):
        await br.publish("Hi!", "test-subject")

        handle.mock.assert_called_once_with("Hi!")
