import pytest

from faststream.kafka import TestKafkaBroker
from faststream.nats import TestNatsBroker
from faststream.rabbit import TestRabbitBroker


@pytest.mark.asyncio
async def test_quickstart_index_kafka():
    from docs.docs_src.getting_started.index.base_kafka import base_handler, broker

    async with TestKafkaBroker(broker) as br:
        await br.publish("", "test")

        base_handler.mock.assert_called_once_with("")


@pytest.mark.asyncio
async def test_quickstart_index_rabbit():
    from docs.docs_src.getting_started.index.base_rabbit import base_handler, broker

    async with TestRabbitBroker(broker) as br:
        await br.publish("", "test")

        base_handler.mock.assert_called_once_with("")


@pytest.mark.asyncio
async def test_quickstart_index_nats():
    from docs.docs_src.getting_started.index.base_nats import base_handler, broker

    async with TestNatsBroker(broker) as br:
        await br.publish("", "test")

        base_handler.mock.assert_called_once_with("")
