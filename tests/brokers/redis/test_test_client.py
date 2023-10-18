import asyncio

import pytest

from faststream import BaseMiddleware
from faststream.redis import RedisBroker, TestRedisBroker
from tests.brokers.base.testclient import BrokerTestclientTestcase


@pytest.mark.asyncio
class TestTestclient(BrokerTestclientTestcase):
    @pytest.mark.redis
    async def test_with_real_testclient(
        self,
        broker: RedisBroker,
        queue: str,
        event: asyncio.Event,
    ):
        @broker.subscriber(queue)
        def subscriber(m):
            event.set()

        async with TestRedisBroker(broker, with_real=True) as br:
            await asyncio.wait(
                (
                    asyncio.create_task(br.publish("hello", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        assert event.is_set()

    async def test_respect_middleware(self, queue):
        routes = []

        class Middleware(BaseMiddleware):
            async def on_receive(self) -> None:
                routes.append(None)
                return await super().on_receive()

        broker = RedisBroker()
        broker.middlewares = (Middleware,)

        @broker.subscriber(queue)
        async def h1():
            ...

        @broker.subscriber(queue + "1")
        async def h2():
            ...

        async with TestRedisBroker(broker) as br:
            await br.publish("", queue)
            await br.publish("", queue + "1")

        assert len(routes) == 2

    @pytest.mark.redis
    async def test_real_respect_middleware(self, queue):
        routes = []

        class Middleware(BaseMiddleware):
            async def on_receive(self) -> None:
                routes.append(None)
                return await super().on_receive()

        broker = RedisBroker()
        broker.middlewares = (Middleware,)

        @broker.subscriber(queue)
        async def h1():
            ...

        @broker.subscriber(queue + "1")
        async def h2():
            ...

        async with TestRedisBroker(broker, with_real=True) as br:
            await br.publish("", queue)
            await br.publish("", queue + "1")
            await h1.wait_call(3)
            await h2.wait_call(3)

        assert len(routes) == 2
