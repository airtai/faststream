import asyncio
from typing import Any

import pytest

from faststream import BaseMiddleware
from faststream.redis import ListSub, RedisBroker, StreamSub, TestRedisBroker
from faststream.redis.testing import FakeProducer
from tests.brokers.base.testclient import BrokerTestclientTestcase


@pytest.mark.asyncio
class TestTestclient(BrokerTestclientTestcase):
    test_class = TestRedisBroker

    def get_broker(self, apply_types: bool = False, **kwargs: Any) -> RedisBroker:
        return RedisBroker(apply_types=apply_types, **kwargs)

    def patch_broker(self, broker: RedisBroker, **kwargs: Any) -> TestRedisBroker:
        return TestRedisBroker(broker, **kwargs)

    @pytest.mark.redis
    async def test_with_real_testclient(
        self,
        queue: str,
        event: asyncio.Event,
    ):
        broker = self.get_broker()

        @broker.subscriber(queue)
        def subscriber(m):
            event.set()

        async with self.patch_broker(broker, with_real=True) as br:
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

        broker = self.get_broker(middlewares=(Middleware,))

        @broker.subscriber(queue)
        async def h1(m): ...

        @broker.subscriber(queue + "1")
        async def h2(m): ...

        async with self.patch_broker(broker) as br:
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

        broker = self.get_broker(middlewares=(Middleware,))

        @broker.subscriber(queue)
        async def h1(m): ...

        @broker.subscriber(queue + "1")
        async def h2(m): ...

        async with self.patch_broker(broker, with_real=True) as br:
            await br.publish("", queue)
            await br.publish("", queue + "1")
            await h1.wait_call(3)
            await h2.wait_call(3)

        assert len(routes) == 2

    async def test_pub_sub_pattern(self):
        broker = self.get_broker()

        @broker.subscriber("test.{name}")
        async def handler(msg):
            return msg

        async with self.patch_broker(broker) as br:
            assert await (await br.request(1, "test.name.useless")).decode() == 1
            handler.mock.assert_called_once_with(1)

    async def test_list(
        self,
        queue: str,
    ):
        broker = self.get_broker()

        @broker.subscriber(list=queue)
        async def handler(msg):
            return msg

        async with self.patch_broker(broker) as br:
            assert await (await br.request(1, list=queue)).decode() == 1
            handler.mock.assert_called_once_with(1)

    async def test_batch_pub_by_default_pub(
        self,
        queue: str,
    ):
        broker = self.get_broker()

        @broker.subscriber(list=ListSub(queue, batch=True))
        async def m(msg):
            pass

        async with self.patch_broker(broker) as br:
            await br.publish("hello", list=queue)
            m.mock.assert_called_once_with(["hello"])

    async def test_batch_pub_by_pub_batch(
        self,
        queue: str,
    ):
        broker = self.get_broker()

        @broker.subscriber(list=ListSub(queue, batch=True))
        async def m(msg):
            pass

        async with self.patch_broker(broker) as br:
            await br.publish_batch("hello", list=queue)
            m.mock.assert_called_once_with(["hello"])

    async def test_batch_publisher_mock(
        self,
        queue: str,
    ):
        broker = self.get_broker()

        batch_list = ListSub(queue + "1", batch=True)
        publisher = broker.publisher(list=batch_list)

        @publisher
        @broker.subscriber(queue)
        async def m(msg):
            return 1, 2, 3

        async with self.patch_broker(broker) as br:
            await br.publish("hello", queue)
            m.mock.assert_called_once_with("hello")
            publisher.mock.assert_called_once_with([1, 2, 3])

    async def test_stream(
        self,
        queue: str,
    ):
        broker = self.get_broker()

        @broker.subscriber(stream=queue)
        async def handler(msg):
            return msg

        async with self.patch_broker(broker) as br:
            assert await (await br.request(1, stream=queue)).decode() == 1
            handler.mock.assert_called_once_with(1)

    async def test_stream_batch_pub_by_default_pub(
        self,
        queue: str,
    ):
        broker = self.get_broker()

        @broker.subscriber(stream=StreamSub(queue, batch=True))
        async def m(msg):
            pass

        async with self.patch_broker(broker) as br:
            await br.publish("hello", stream=queue)
            m.mock.assert_called_once_with(["hello"])

    async def test_stream_publisher(
        self,
        queue: str,
    ):
        broker = self.get_broker()

        batch_stream = StreamSub(queue + "1")
        publisher = broker.publisher(stream=batch_stream)

        @publisher
        @broker.subscriber(queue)
        async def m(msg):
            return 1, 2, 3

        async with self.patch_broker(broker) as br:
            await br.publish("hello", queue)
            m.mock.assert_called_once_with("hello")
            publisher.mock.assert_called_once_with([1, 2, 3])

    async def test_publish_to_none(
        self,
        queue: str,
    ):
        broker = self.get_broker()

        async with self.patch_broker(broker) as br:
            with pytest.raises(ValueError):  # noqa: PT011
                await br.publish("hello")

    @pytest.mark.redis
    async def test_broker_gets_patched_attrs_within_cm(self):
        await super().test_broker_gets_patched_attrs_within_cm(FakeProducer)

    @pytest.mark.redis
    async def test_broker_with_real_doesnt_get_patched(self):
        await super().test_broker_with_real_doesnt_get_patched()

    @pytest.mark.redis
    async def test_broker_with_real_patches_publishers_and_subscribers(
        self, queue: str
    ):
        await super().test_broker_with_real_patches_publishers_and_subscribers(queue)

    @pytest.mark.redis
    async def test_lazy_name_initialization(self, queue: str, event):
        list_sub = ListSub()
        consume_broker = self.get_broker()
        publisher = consume_broker.publisher(list=list_sub)

        @publisher
        @consume_broker.subscriber(list=list_sub)
        async def m(msg):
            event.set()

        list_sub.name = queue

        async with self.patch_broker(consume_broker, with_real=True) as br:
            await br.start()
            await asyncio.wait(
                (
                    asyncio.create_task(br.publish("hello", list=queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )
            m.mock.assert_called_once_with("hello")
            publisher.mock.assert_called_once()
        assert event.is_set()

    @pytest.mark.redis
    async def test_lazy_add_prefix(self, queue: str):
        list_sub = ListSub()
        list_sub.name = queue
        new_list_sub = list_sub.add_prefix(prefix="t")
        assert list_sub is not new_list_sub