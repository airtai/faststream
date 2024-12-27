from unittest.mock import AsyncMock

import pytest

from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue
from faststream.rabbit.helpers.declarer import RabbitDeclarer


@pytest.mark.asyncio
async def test_declare_queue(async_mock, queue: str):
    declarer = RabbitDeclarer(async_mock)

    q1 = await declarer.declare_queue(RabbitQueue(queue))
    q2 = await declarer.declare_queue(RabbitQueue(queue))

    assert q1 is q2
    async_mock.declare_queue.assert_awaited_once()


@pytest.mark.asyncio
async def test_declare_exchange(
    async_mock,
    queue: str,
):
    declarer = RabbitDeclarer(async_mock)

    ex1 = await declarer.declare_exchange(RabbitExchange(queue))
    ex2 = await declarer.declare_exchange(RabbitExchange(queue))

    assert ex1 is ex2
    async_mock.declare_exchange.assert_awaited_once()


@pytest.mark.asyncio
async def test_declare_nested_exchange_cash_nested(
    async_mock,
    queue: str,
):
    declarer = RabbitDeclarer(async_mock)

    exchange = RabbitExchange(queue)

    await declarer.declare_exchange(RabbitExchange(queue + "1", bind_to=exchange))
    assert async_mock.declare_exchange.await_count == 2

    await declarer.declare_exchange(exchange)
    assert async_mock.declare_exchange.await_count == 2


@pytest.mark.asyncio
async def test_publisher_declare(
    async_mock,
    queue: str,
):
    declarer = RabbitDeclarer(async_mock)

    broker = RabbitBroker()
    broker._connection = async_mock
    broker.declarer = declarer

    @broker.publisher(queue, queue)
    async def f(): ...

    await broker.start()

    assert not async_mock.declare_queue.await_count
    async_mock.declare_exchange.assert_awaited_once()


@pytest.mark.asyncio
async def test_declare_binding(
    async_mock,
    queue: str,
):
    queue_mock = AsyncMock()
    async_mock.declare_queue.side_effect = lambda *_, **__: queue_mock

    declarer = RabbitDeclarer(async_mock)

    q1 = RabbitQueue(queue)
    q2 = RabbitQueue(queue)

    exch1 = RabbitExchange(queue)
    exch2 = RabbitExchange(queue)

    await declarer.declare_binding(q1, exch1)
    await declarer.declare_binding(q2, exch2)

    assert async_mock.declare_exchange.await_count == 1
    assert async_mock.declare_queue.await_count == 1

    queue_mock.bind.assert_awaited()
    assert queue_mock.bind.await_count == 2
