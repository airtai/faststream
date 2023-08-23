import asyncio
from contextlib import asynccontextmanager
from typing import Type
from unittest.mock import Mock

import pytest

from propan.broker.core.abc import BrokerUsecase


@pytest.mark.asyncio
class LocalMiddlewareTestcase:
    broker_class: Type[BrokerUsecase]

    @pytest.fixture
    def raw_broker(self):
        return None

    def patch_broker(
        self, raw_broker: BrokerUsecase, broker: BrokerUsecase
    ) -> BrokerUsecase:
        return broker

    async def test_local_middleware(
        self, event: asyncio.Event, queue: str, mock: Mock, raw_broker
    ):
        @asynccontextmanager
        async def mid(msg):
            mock.start(msg)
            try:
                yield
            finally:
                mock.end()

        broker = self.broker_class()

        @broker.subscriber(queue, middlewares=(mid,))
        async def handler(m):
            event.set()
            return ""

        broker = self.patch_broker(raw_broker, broker)

        async with broker:
            await broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(broker.publish("", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        assert event.is_set()
        mock.start.assert_called_once()
        mock.end.assert_called_once()

    async def test_local_middleware_not_shared_between_subscribers(
        self, queue: str, mock: Mock, raw_broker
    ):
        event1 = asyncio.Event()
        event2 = asyncio.Event()

        @asynccontextmanager
        async def mid(msg):
            mock.start(msg)
            try:
                yield
            finally:
                mock.end()

        broker = self.broker_class()

        @broker.subscriber(queue)
        @broker.subscriber(queue + "1", middlewares=(mid,))
        async def handler(m):
            if event1.is_set():
                event2.set()
            else:
                event1.set()
            mock()
            return ""

        broker = self.patch_broker(raw_broker, broker)

        async with broker:
            await broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(broker.publish("", queue)),
                    asyncio.create_task(broker.publish("", queue + "1")),
                    asyncio.create_task(event1.wait()),
                    asyncio.create_task(event2.wait()),
                ),
                timeout=3,
            )

        assert event1.is_set()
        assert event2.is_set()
        mock.start.assert_called_once()
        mock.end.assert_called_once()
        assert mock.call_count == 2

    async def test_local_middleware_not_shared_between_filters(
        self, queue: str, mock: Mock, raw_broker
    ):
        event1 = asyncio.Event()
        event2 = asyncio.Event()

        @asynccontextmanager
        async def mid(msg):
            mock.start(msg)
            try:
                yield
            finally:
                mock.end()

        broker = self.broker_class()

        @broker.subscriber(queue, filter=lambda m: m.content_type == "application/json")
        async def handler(m):
            event2.set()
            mock()
            return ""

        @broker.subscriber(queue, middlewares=(mid,))
        async def handler2(m):
            event1.set()
            mock()
            return ""

        broker = self.patch_broker(raw_broker, broker)

        async with broker:
            await broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(broker.publish({"msg": "hi"}, queue)),
                    asyncio.create_task(broker.publish("", queue)),
                    asyncio.create_task(event1.wait()),
                    asyncio.create_task(event2.wait()),
                ),
                timeout=3,
            )

        assert event1.is_set()
        assert event2.is_set()
        mock.start.assert_called_once()
        mock.end.assert_called_once()
        assert mock.call_count == 2


@pytest.mark.asyncio
class MiddlewareTestcase(LocalMiddlewareTestcase):
    async def test_global_middleware(
        self, event: asyncio.Event, queue: str, mock: Mock, raw_broker
    ):
        @asynccontextmanager
        async def mid(msg):
            mock.start(msg)
            try:
                yield
            finally:
                mock.end()

        broker = self.broker_class(
            middlewares=(mid,),
        )

        @broker.subscriber(queue)
        async def handler(m):
            event.set()
            return ""

        broker = self.patch_broker(raw_broker, broker)

        async with broker:
            await broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(broker.publish("", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        assert event.is_set()
        mock.start.assert_called_once()
        mock.end.assert_called_once()
