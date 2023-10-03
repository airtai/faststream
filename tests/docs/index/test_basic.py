import pytest

from faststream.kafka import TestKafkaBroker
from faststream.nats import TestNatsBroker
from faststream.rabbit import TestRabbitBroker


@pytest.mark.asyncio
async def test_index_kafka_base():
    from docs.docs_src.index.basic_kafka import broker, handle_msg

    async with TestKafkaBroker(broker) as br:
        await br.publish({"user": "John", "user_id": 1}, "in-topic")

        handle_msg.mock.assert_called_once_with({"user": "John", "user_id": 1})

        list(br._publishers.values())[0].mock.assert_called_once_with(
            "User: 1 - John registered"
        )


@pytest.mark.asyncio
async def test_index_rabbit_base():
    from docs.docs_src.index.basic_rabbit import broker, handle_msg

    async with TestRabbitBroker(broker) as br:
        await br.publish({"user": "John", "user_id": 1}, "in-queue")

        handle_msg.mock.assert_called_once_with({"user": "John", "user_id": 1})

        list(br._publishers.values())[0].mock.assert_called_once_with(
            "User: 1 - John registered"
        )


@pytest.mark.asyncio
async def test_index_nats_base():
    from docs.docs_src.index.basic_nats import broker, handle_msg

    async with TestNatsBroker(broker) as br:
        await br.publish({"user": "John", "user_id": 1}, "in-subject")

        handle_msg.mock.assert_called_once_with({"user": "John", "user_id": 1})

        list(br._publishers.values())[0].mock.assert_called_once_with(
            "User: 1 - John registered"
        )
