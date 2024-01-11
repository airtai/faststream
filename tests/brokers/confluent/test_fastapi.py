import asyncio
from typing import List, Type, TypeVar
from unittest.mock import Mock

import pytest

from faststream import context
from faststream.broker.core.asynchronous import BrokerAsyncUsecase
from faststream.broker.fastapi.context import Context
from faststream.broker.fastapi.router import StreamRouter
from faststream.confluent.fastapi import KafkaRouter
from faststream.confluent.test import TestKafkaBroker, build_message
from tests.brokers.base.fastapi import FastAPILocalTestcase

Broker = TypeVar("Broker", bound=BrokerAsyncUsecase)


@pytest.mark.asyncio()
class FastAPITestcase:  # noqa: D101
    router_class: Type[StreamRouter[BrokerAsyncUsecase]]

    async def test_base_real(self, mock: Mock, queue: str, event: asyncio.Event):
        router = self.router_class()

        @router.subscriber(queue, auto_offset_reset="earliest")
        async def hello(msg):
            event.set()
            return mock(msg)

        async with router.broker:
            await router.broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(router.broker.publish("hi", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=10,
            )

        assert event.is_set()
        mock.assert_called_with("hi")

    async def test_context(self, mock: Mock, queue: str, event: asyncio.Event):
        router = self.router_class()

        context_key = "message.headers"

        @router.subscriber(queue, auto_offset_reset="earliest")
        async def hello(msg=Context(context_key)):
            event.set()
            return mock(msg == context.resolve(context_key))

        async with router.broker:
            await router.broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(router.broker.publish("", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=10,
            )

        assert event.is_set()
        mock.assert_called_with(True)

    async def test_initial_context(self, queue: str, event: asyncio.Event):
        router = self.router_class()

        @router.subscriber(queue, auto_offset_reset="earliest")
        async def hello(msg: int, data=Context(queue, initial=set)):
            data.add(msg)
            if len(data) == 2:
                event.set()

        async with router.broker:
            await router.broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(router.broker.publish(1, queue)),
                    asyncio.create_task(router.broker.publish(2, queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=10,
            )

        assert event.is_set()
        assert context.get(queue) == {1, 2}
        context.reset_global(queue)

    async def test_double_real(self, mock: Mock, queue: str, event: asyncio.Event):
        event2 = asyncio.Event()
        router = self.router_class()

        @router.subscriber(queue, auto_offset_reset="earliest")
        @router.subscriber(queue + "2", auto_offset_reset="earliest")
        async def hello(msg):
            if event.is_set():
                event2.set()
            else:
                event.set()
            mock()

        async with router.broker:
            await router.broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(router.broker.publish("hi", queue)),
                    asyncio.create_task(router.broker.publish("hi", queue + "2")),
                    asyncio.create_task(event.wait()),
                    asyncio.create_task(event2.wait()),
                ),
                timeout=10,
            )

        assert event.is_set()
        assert event2.is_set()
        assert mock.call_count == 2

    async def test_base_publisher_real(
        self, mock: Mock, queue: str, event: asyncio.Event
    ):
        router = self.router_class()

        @router.subscriber(queue, auto_offset_reset="earliest")
        @router.publisher(queue + "resp")
        async def m():
            return "hi"

        @router.subscriber(queue + "resp", auto_offset_reset="earliest")
        async def resp(msg):
            event.set()
            mock(msg)

        async with router.broker:
            await router.broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(router.broker.publish("", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=10,
            )

        assert event.is_set()
        mock.assert_called_once_with("hi")

@pytest.mark.confluent()
class TestRabbitRouter(FastAPITestcase):  # noqa: D101
    router_class = KafkaRouter

    async def test_batch_real(
        self,
        mock: Mock,
        queue: str,
        event: asyncio.Event,
    ):
        router = KafkaRouter()

        @router.subscriber(queue, batch=True, auto_offset_reset="earliest")
        async def hello(msg: List[str]):
            event.set()
            return mock(msg)

        async with router.broker:
            await router.broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(router.broker.publish("hi", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=10,
            )

        assert event.is_set()
        mock.assert_called_with(["hi"])


class TestRouterLocal(FastAPILocalTestcase):  # noqa: D101
    router_class = KafkaRouter
    broker_test = staticmethod(TestKafkaBroker)
    build_message = staticmethod(build_message)

    async def test_batch_testclient(
        self,
        mock: Mock,
        queue: str,
        event: asyncio.Event,
    ):
        router = KafkaRouter()

        @router.subscriber(queue, batch=True, auto_offset_reset="earliest")
        async def hello(msg: List[str]):
            event.set()
            return mock(msg)

        async with TestKafkaBroker(router.broker):
            await asyncio.wait(
                (
                    asyncio.create_task(router.broker.publish("hi", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=10,
            )

        assert event.is_set()
        mock.assert_called_with(["hi"])
