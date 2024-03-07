import asyncio

import pytest

from faststream import BaseMiddleware
from faststream.redis import ListSub, RedisBroker, StreamSub, TestRedisBroker
from tests.brokers.base.testclient import BrokerTestclientTestcase


@pytest.mark.asyncio()
class TestTestclient(BrokerTestclientTestcase):  # noqa: D101
    @pytest.mark.redis()
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
        async def h1(): ...

        @broker.subscriber(queue + "1")
        async def h2(): ...

        async with TestRedisBroker(broker) as br:
            await br.publish("", queue)
            await br.publish("", queue + "1")

        assert len(routes) == 2

    @pytest.mark.redis()
    async def test_real_respect_middleware(self, queue):
        routes = []

        class Middleware(BaseMiddleware):
            async def on_receive(self) -> None:
                routes.append(None)
                return await super().on_receive()

        broker = RedisBroker()
        broker.middlewares = (Middleware,)

        @broker.subscriber(queue)
        async def h1(): ...

        @broker.subscriber(queue + "1")
        async def h2(): ...

        async with TestRedisBroker(broker, with_real=True) as br:
            await br.publish("", queue)
            await br.publish("", queue + "1")
            await h1.wait_call(3)
            await h2.wait_call(3)

        assert len(routes) == 2

    async def test_pub_sub_pattern(
        self,
        test_broker: RedisBroker,
    ):
        @test_broker.subscriber("test.{name}")
        async def handler(msg):
            return msg

        await test_broker.start()

        assert await test_broker.publish(1, "test.name.useless", rpc=True) == 1
        handler.mock.assert_called_once_with(1)

    async def test_list(
        self,
        test_broker: RedisBroker,
        queue: str,
    ):
        @test_broker.subscriber(list=queue)
        async def handler(msg):
            return msg

        await test_broker.start()

        assert await test_broker.publish(1, list=queue, rpc=True) == 1
        handler.mock.assert_called_once_with(1)

    async def test_batch_pub_by_default_pub(
        self,
        test_broker: RedisBroker,
        queue: str,
    ):
        @test_broker.subscriber(list=ListSub(queue, batch=True))
        async def m():
            pass

        await test_broker.start()
        await test_broker.publish("hello", list=queue)
        m.mock.assert_called_once_with(["hello"])

    async def test_batch_pub_by_pub_batch(
        self,
        test_broker: RedisBroker,
        queue: str,
    ):
        @test_broker.subscriber(list=ListSub(queue, batch=True))
        async def m():
            pass

        await test_broker.start()
        await test_broker.publish_batch("hello", list=queue)
        m.mock.assert_called_once_with(["hello"])

    async def test_batch_publisher_mock(
        self,
        test_broker: RedisBroker,
        queue: str,
    ):
        batch_list = ListSub(queue + "1", batch=True)
        publisher = test_broker.publisher(list=batch_list)

        @publisher
        @test_broker.subscriber(queue)
        async def m():
            return 1, 2, 3

        await test_broker.start()
        await test_broker.publish("hello", queue)
        m.mock.assert_called_once_with("hello")
        publisher.mock.assert_called_once_with([1, 2, 3])

    async def test_stream(
        self,
        test_broker: RedisBroker,
        queue: str,
    ):
        @test_broker.subscriber(stream=queue)
        async def handler(msg):
            return msg

        await test_broker.start()

        assert await test_broker.publish(1, stream=queue, rpc=True) == 1
        handler.mock.assert_called_once_with(1)

    async def test_stream_batch_pub_by_default_pub(
        self,
        test_broker: RedisBroker,
        queue: str,
    ):
        @test_broker.subscriber(stream=StreamSub(queue, batch=True))
        async def m():
            pass

        await test_broker.start()
        await test_broker.publish("hello", stream=queue)
        m.mock.assert_called_once_with(["hello"])

    async def test_stream_publisher(
        self,
        test_broker: RedisBroker,
        queue: str,
    ):
        batch_stream = StreamSub(queue + "1")
        publisher = test_broker.publisher(stream=batch_stream)

        @publisher
        @test_broker.subscriber(queue)
        async def m():
            return 1, 2, 3

        await test_broker.start()
        await test_broker.publish("hello", queue)
        m.mock.assert_called_once_with("hello")
        publisher.mock.assert_called_once_with([1, 2, 3])

    async def test_publish_to_none(
        self,
        test_broker: RedisBroker,
        queue: str,
    ):
        await test_broker.start()
        with pytest.raises(ValueError):  # noqa: PT011
            await test_broker.publish("hello")
