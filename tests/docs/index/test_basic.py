import pytest

from faststream.kafka import TestKafkaBroker
from faststream.nats import TestNatsBroker
from faststream.rabbit import TestRabbitBroker
from faststream.redis import TestRedisBroker


@pytest.mark.asyncio()
async def test_index_kafka_base():
    from docs.docs_src.index.kafka.basic import broker, handle_msg

    async with TestKafkaBroker(broker) as br:
        await br.publish({"user": "John", "user_id": 1}, "in-topic")

        handle_msg.mock.assert_called_once_with({"user": "John", "user_id": 1})

        list(br._publishers.values())[0].mock.assert_called_once_with(  # noqa: RUF015
            "User: 1 - John registered"
        )


@pytest.mark.asyncio()
async def test_index_rabbit_base():
    from docs.docs_src.index.rabbit.basic import broker, handle_msg

    async with TestRabbitBroker(broker) as br:
        await br.publish({"user": "John", "user_id": 1}, "in-queue")

        handle_msg.mock.assert_called_once_with({"user": "John", "user_id": 1})

        list(br._publishers.values())[0].mock.assert_called_once_with(  # noqa: RUF015
            "User: 1 - John registered"
        )


@pytest.mark.asyncio()
async def test_index_nats_base():
    from docs.docs_src.index.nats.basic import broker, handle_msg

    async with TestNatsBroker(broker) as br:
        await br.publish({"user": "John", "user_id": 1}, "in-subject")

        handle_msg.mock.assert_called_once_with({"user": "John", "user_id": 1})

        list(br._publishers.values())[0].mock.assert_called_once_with(  # noqa: RUF015
            "User: 1 - John registered"
        )


@pytest.mark.asyncio()
async def test_index_redis_base():
    from docs.docs_src.index.redis.basic import broker, handle_msg

    async with TestRedisBroker(broker) as br:
        await br.publish({"user": "John", "user_id": 1}, "in-channel")

        handle_msg.mock.assert_called_once_with({"user": "John", "user_id": 1})

        list(br._publishers.values())[0].mock.assert_called_once_with(  # noqa: RUF015
            "User: 1 - John registered"
        )
