import asyncio
from typing import List
from unittest.mock import MagicMock

import pytest

from faststream.nats import JStream, PullSub
from faststream.nats.fastapi import NatsRouter
from faststream.nats.test import TestNatsBroker, build_message
from tests.brokers.base.fastapi import FastAPILocalTestcase, FastAPITestcase


@pytest.mark.nats()
class TestRouter(FastAPITestcase):  # noqa: D101
    router_class = NatsRouter

    async def test_consume_batch(
        self,
        queue: str,
        stream: JStream,
        event: asyncio.Event,
        mock: MagicMock,
    ):
        router = NatsRouter()

        @router.subscriber(
            queue,
            stream=stream,
            pull_sub=PullSub(1, batch=True),
        )
        def subscriber(m: List[str]):
            mock(m)
            event.set()

        async with router.broker:
            await router.broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(router.broker.publish(b"hello", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        assert event.is_set()
        mock.assert_called_once_with(["hello"])


class TestRouterLocal(FastAPILocalTestcase):  # noqa: D101
    router_class = NatsRouter
    broker_test = staticmethod(TestNatsBroker)
    build_message = staticmethod(build_message)

    async def test_consume_batch(
        self,
        queue: str,
        stream: JStream,
        event: asyncio.Event,
        mock: MagicMock,
    ):
        router = NatsRouter()

        @router.subscriber(
            queue,
            stream=stream,
            pull_sub=PullSub(1, batch=True),
        )
        def subscriber(m: List[str]):
            mock(m)
            event.set()

        async with self.broker_test(router.broker):
            await asyncio.wait(
                (
                    asyncio.create_task(router.broker.publish(b"hello", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        assert event.is_set()
        mock.assert_called_once_with(["hello"])

    async def test_path(self, queue: str):
        router = self.router_class()

        @router.subscriber(queue + ".{name}")
        async def hello(name):
            return name

        async with self.broker_test(router.broker):
            r = await router.broker.publish(
                "hi",
                f"{queue}.john",
                rpc=True,
                rpc_timeout=0.5,
            )
            assert r == "john"
