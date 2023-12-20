import pytest

from faststream import Path
from faststream.nats import NatsBroker, TestNatsBroker
from faststream.rabbit import (
    ExchangeType,
    RabbitBroker,
    RabbitExchange,
    RabbitQueue,
    TestRabbitBroker,
)
from faststream.redis import RedisBroker, TestRedisBroker


@pytest.mark.asyncio()
async def test_nats_path():
    broker = NatsBroker()

    @broker.subscriber("in.{name}.{id}")
    async def h(
        name: str = Path(),
        id_: int = Path("id"),
    ):
        assert name == "john"
        assert id_ == 1
        return 1

    async with TestNatsBroker(broker) as br:
        assert (
            await br.publish(
                "",
                "in.john.1",
                rpc=True,
                rpc_timeout=1.0,
            )
            == 1
        )


@pytest.mark.asyncio()
async def test_redis_path():
    broker = RedisBroker()

    @broker.subscriber("in.{name}.{id}")
    async def h(
        name: str = Path(),
        id_: int = Path("id"),
    ):
        assert name == "john"
        assert id_ == 1
        return 1

    async with TestRedisBroker(broker) as br:
        assert (
            await br.publish(
                "",
                "in.john.1",
                rpc=True,
                rpc_timeout=1.0,
            )
            == 1
        )


@pytest.mark.asyncio()
async def test_rabbit_path():
    broker = RabbitBroker()

    @broker.subscriber(
        RabbitQueue(
            "test",
            routing_key="in.{name}.{id}",
        ),
        RabbitExchange(
            "test",
            type=ExchangeType.TOPIC,
        ),
    )
    async def h(
        name: str = Path(),
        id_: int = Path("id"),
    ):
        assert name == "john"
        assert id_ == 1
        return 1

    async with TestRabbitBroker(broker) as br:
        assert (
            await br.publish(
                "",
                "in.john.1",
                "test",
                rpc=True,
                rpc_timeout=1.0,
            )
            == 1
        )
