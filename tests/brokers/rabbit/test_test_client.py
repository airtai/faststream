import asyncio
from unittest.mock import Mock

import pytest

from faststream import BaseMiddleware
from faststream.rabbit import (
    ExchangeType,
    RabbitBroker,
    RabbitExchange,
    RabbitQueue,
    TestRabbitBroker,
)
from faststream.rabbit.annotations import RabbitMessage
from tests.brokers.base.testclient import BrokerTestclientTestcase


@pytest.mark.asyncio
class TestTestclient(BrokerTestclientTestcase):
    @pytest.mark.rabbit
    async def test_with_real_testclient(
        self,
        broker: RabbitBroker,
        queue: str,
        event: asyncio.Event,
    ):
        @broker.subscriber(queue)
        def subscriber(m):
            event.set()

        async with TestRabbitBroker(broker, with_real=True) as br:
            await asyncio.wait(
                (
                    asyncio.create_task(br.publish("hello", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        assert event.is_set()

    async def test_direct(
        self,
        test_broker: RabbitBroker,
        queue: str,
    ):
        @test_broker.subscriber(queue)
        async def handler(m):
            return 1

        @test_broker.subscriber(queue + "1", exchange="test")
        async def handler2(m):
            return 2

        await test_broker.start()
        assert 1 == await test_broker.publish("", queue, rpc=True)
        assert 2 == await test_broker.publish(
            "", queue + "1", exchange="test", rpc=True
        )
        assert None is await test_broker.publish("", exchange="test2", rpc=True)

    async def test_fanout(
        self,
        test_broker: RabbitBroker,
        queue: str,
    ):
        mock = Mock()

        exch = RabbitExchange("test", type=ExchangeType.FANOUT)

        @test_broker.subscriber(queue, exchange=exch)
        async def handler(m):
            mock()

        await test_broker.start()
        await test_broker.publish("", exchange=exch, rpc=True)
        assert None is await test_broker.publish("", exchange="test2", rpc=True)

        assert mock.call_count == 1

    async def test_topic(
        self,
        test_broker: RabbitBroker,
    ):
        exch = RabbitExchange("test", type=ExchangeType.TOPIC)

        @test_broker.subscriber(
            RabbitQueue("logs", routing_key="*.info"), exchange=exch
        )
        async def handler(m):
            return 1

        @test_broker.subscriber(
            RabbitQueue("logs2", routing_key="*.error"), exchange=exch
        )
        async def handler2(m):
            return 2

        await test_broker.start()
        assert 1 == await test_broker.publish("", "logs.info", exchange=exch, rpc=True)
        assert 2 == await test_broker.publish("", "logs.error", exchange=exch, rpc=True)
        assert None is await test_broker.publish("", "logs.error", rpc=True)

    async def test_header(
        self,
        test_broker: RabbitBroker,
    ):
        q1 = RabbitQueue(
            "test-queue-2",
            bind_arguments={"key": 2, "key2": 2, "x-match": "any"},
        )
        q2 = RabbitQueue(
            "test-queue-3",
            bind_arguments={"key": 2, "key2": 2, "x-match": "all"},
        )
        q3 = RabbitQueue(
            "test-queue-4",
            bind_arguments={},
        )
        exch = RabbitExchange("exchange", type=ExchangeType.HEADERS)

        @test_broker.subscriber(q2, exch)
        async def handler2():
            return 2

        @test_broker.subscriber(q1, exch)
        async def handler():
            return 1

        @test_broker.subscriber(q3, exch)
        async def handler3():
            return 3

        await test_broker.start()
        assert 2 == await test_broker.publish(
            exchange=exch, rpc=True, headers={"key": 2, "key2": 2}
        )
        assert 1 == await test_broker.publish(
            exchange=exch, rpc=True, headers={"key": 2}
        )
        assert 3 == await test_broker.publish(exchange=exch, rpc=True, headers={})

    async def test_consume_manual_ack(
        self,
        queue: str,
        exchange: RabbitExchange,
        test_broker: RabbitBroker,
    ):
        consume = asyncio.Event()
        consume2 = asyncio.Event()
        consume3 = asyncio.Event()

        @test_broker.subscriber(queue=queue, exchange=exchange, retry=1)
        async def handler(msg: RabbitMessage):
            await msg.raw_message.ack()
            consume.set()

        @test_broker.subscriber(queue=queue + "1", exchange=exchange, retry=1)
        async def handler2(msg: RabbitMessage):
            await msg.raw_message.nack()
            consume2.set()
            raise ValueError()

        @test_broker.subscriber(queue=queue + "2", exchange=exchange, retry=1)
        async def handler3(msg: RabbitMessage):
            await msg.raw_message.reject()
            consume3.set()
            raise ValueError()

        await test_broker.start()
        async with test_broker:
            await test_broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(
                        test_broker.publish("hello", queue=queue, exchange=exchange)
                    ),
                    asyncio.create_task(
                        test_broker.publish(
                            "hello", queue=queue + "1", exchange=exchange
                        )
                    ),
                    asyncio.create_task(
                        test_broker.publish(
                            "hello", queue=queue + "2", exchange=exchange
                        )
                    ),
                    asyncio.create_task(consume.wait()),
                    asyncio.create_task(consume2.wait()),
                    asyncio.create_task(consume3.wait()),
                ),
                timeout=3,
            )

        assert consume.is_set()
        assert consume2.is_set()
        assert consume3.is_set()

    async def test_respect_middleware(self, queue):
        routes = []

        class Middleware(BaseMiddleware):
            async def on_receive(self) -> None:
                routes.append(None)
                return await super().on_receive()

        broker = RabbitBroker()
        broker.middlewares = (Middleware,)

        @broker.subscriber(queue)
        async def h1():
            ...

        @broker.subscriber(queue + "1")
        async def h2():
            ...

        async with TestRabbitBroker(broker) as br:
            await br.publish("", queue)
            await br.publish("", queue + "1")

        assert len(routes) == 2

    @pytest.mark.rabbit
    async def test_real_respect_middleware(self, queue):
        routes = []

        class Middleware(BaseMiddleware):
            async def on_receive(self) -> None:
                routes.append(None)
                return await super().on_receive()

        broker = RabbitBroker()
        broker.middlewares = (Middleware,)

        @broker.subscriber(queue)
        async def h1():
            ...

        @broker.subscriber(queue + "1")
        async def h2():
            ...

        async with TestRabbitBroker(broker, with_real=True) as br:
            await br.publish("", queue)
            await br.publish("", queue + "1")
            await h1.wait_call(3)
            await h2.wait_call(3)

        assert len(routes) == 2
