import asyncio
from unittest.mock import Mock

import pytest

from faststream import Path
from tests.marks import require_aiokafka, require_aiopika, require_nats, require_redis


@pytest.mark.asyncio
@require_aiokafka
async def test_aiokafka_path():
    from faststream.kafka import KafkaBroker, TestKafkaBroker

    broker = KafkaBroker()

    @broker.subscriber(pattern="in.{name}.{id}")
    async def h(
        name: str = Path(),
        id_: int = Path("id"),
    ):
        assert name == "john"
        assert id_ == 1
        return 1

    async with TestKafkaBroker(broker) as br:
        assert (
            await br.publish(
                "",
                "in.john.1",
                rpc=True,
                rpc_timeout=1.0,
            )
            == 1
        )


@pytest.mark.asyncio
@require_nats
async def test_nats_path():
    from faststream.nats import NatsBroker, TestNatsBroker

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


@pytest.mark.asyncio
@pytest.mark.nats
@require_nats
async def test_nats_kv_path(
    queue: str,
    event: asyncio.Event,
    mock: Mock,
):
    from faststream.nats import NatsBroker

    broker = NatsBroker()

    @broker.subscriber("in.{name}.{id}", kv_watch=queue)
    async def h(
        msg: int,
        name: str = Path(),
        id_: int = Path("id"),
    ):
        mock(msg == 1 and name == "john" and id_ == 1)
        event.set()

    async with broker:
        await broker.start()

        kv = await broker.key_value(queue)

        await asyncio.wait(
            (
                asyncio.create_task(kv.put("in.john.1", b"1")),
                asyncio.create_task(event.wait()),
            ),
            timeout=3,
        )

    assert event.is_set()
    mock.assert_called_once_with(True)


@pytest.mark.asyncio
@require_nats
async def test_nats_batch_path():
    from faststream.nats import NatsBroker, PullSub, TestNatsBroker

    broker = NatsBroker()

    @broker.subscriber("in.{name}.{id}", stream="test", pull_sub=PullSub(batch=True))
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


@pytest.mark.asyncio
@require_redis
async def test_redis_path():
    from faststream.redis import RedisBroker, TestRedisBroker

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


@pytest.mark.asyncio
@require_aiopika
async def test_rabbit_path():
    from faststream.rabbit import (
        ExchangeType,
        RabbitBroker,
        RabbitExchange,
        RabbitQueue,
        TestRabbitBroker,
    )

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
