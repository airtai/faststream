import asyncio
from unittest.mock import Mock

import pytest

from faststream.redis import ListSub, RedisRouter, StreamSub
from faststream.redis.fastapi import RedisRouter as StreamRouter
from tests.brokers.base.fastapi import FastAPILocalTestcase, FastAPITestcase

from .basic import RedisMemoryTestcaseConfig


@pytest.mark.redis()
class TestRouter(FastAPITestcase):
    router_class = StreamRouter
    broker_router_class = RedisRouter

    async def test_path(
        self,
        queue: str,
        mock: Mock,
    ) -> None:
        event = asyncio.Event()

        router = self.router_class()

        @router.subscriber("in.{name}")
        def subscriber(msg: str, name: str) -> None:
            mock(msg=msg, name=name)
            event.set()

        async with router.broker:
            await router.broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(router.broker.publish("hello", "in.john")),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        assert event.is_set()
        mock.assert_called_once_with(msg="hello", name="john")

    async def test_connection_params(self, settings) -> None:
        broker = self.router_class(
            host="fake-host",
            port=6377,
        ).broker  # kwargs will be ignored
        await broker.connect(
            host=settings.host,
            port=settings.port,
        )
        await broker._connection.ping()
        await broker.close()

    async def test_batch_real(
        self,
        mock: Mock,
        queue: str,
    ) -> None:
        event = asyncio.Event()

        router = self.router_class()

        @router.subscriber(list=ListSub(queue, batch=True, max_records=1))
        async def hello(msg: list[str]):
            event.set()
            return mock(msg)

        async with router.broker:
            await router.broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(router.broker.publish("hi", list=queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        assert event.is_set()
        mock.assert_called_with(["hi"])

    @pytest.mark.slow()
    async def test_consume_stream(
        self,
        mock: Mock,
        queue,
    ) -> None:
        event = asyncio.Event()

        router = self.router_class()

        @router.subscriber(stream=StreamSub(queue, polling_interval=10))
        async def handler(msg) -> None:
            mock(msg)
            event.set()

        async with router.broker:
            await router.broker.start()
            await asyncio.sleep(0.5)

            await asyncio.wait(
                (
                    asyncio.create_task(router.broker.publish("hello", stream=queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        mock.assert_called_once_with("hello")

    @pytest.mark.slow()
    async def test_consume_stream_batch(
        self,
        mock: Mock,
        queue,
    ) -> None:
        event = asyncio.Event()

        router = self.router_class()

        @router.subscriber(stream=StreamSub(queue, polling_interval=10, batch=True))
        async def handler(msg: list[str]) -> None:
            mock(msg)
            event.set()

        async with router.broker:
            await router.broker.start()
            await asyncio.sleep(0.5)

            await asyncio.wait(
                (
                    asyncio.create_task(router.broker.publish("hello", stream=queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        mock.assert_called_once_with(["hello"])


class TestRouterLocal(RedisMemoryTestcaseConfig, FastAPILocalTestcase):
    router_class = StreamRouter
    broker_router_class = RedisRouter

    async def test_batch_testclient(
        self,
        mock: Mock,
        queue: str,
    ) -> None:
        event = asyncio.Event()

        router = self.router_class()

        @router.subscriber(list=ListSub(queue, batch=True, max_records=1))
        async def hello(msg: list[str]):
            event.set()
            return mock(msg)

        async with self.patch_broker(router.broker) as br:
            await asyncio.wait(
                (
                    asyncio.create_task(br.publish("hi", list=queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        assert event.is_set()
        mock.assert_called_with(["hi"])

    async def test_stream_batch_testclient(
        self,
        mock: Mock,
        queue: str,
    ) -> None:
        event = asyncio.Event()

        router = self.router_class()

        @router.subscriber(stream=StreamSub(queue, batch=True))
        async def hello(msg: list[str]):
            event.set()
            return mock(msg)

        async with self.patch_broker(router.broker) as br:
            await asyncio.wait(
                (
                    asyncio.create_task(br.publish("hi", stream=queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        assert event.is_set()
        mock.assert_called_with(["hi"])

    async def test_path(self, queue: str) -> None:
        router = self.router_class()

        @router.subscriber(queue + ".{name}")
        async def hello(name):
            return name

        async with self.patch_broker(router.broker) as br:
            r = await br.request(
                "hi",
                f"{queue}.john",
                timeout=0.5,
            )
            assert await r.decode() == "john"
