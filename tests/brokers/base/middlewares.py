import asyncio
from contextlib import asynccontextmanager
from typing import Type, Any
from unittest.mock import Mock

import pytest

from faststream.broker.core.usecase import BrokerUsecase
from faststream.broker.middlewares import BaseMiddleware


@pytest.mark.asyncio()
class LocalMiddlewareTestcase:
    broker_class: Type[BrokerUsecase]
    timeout: int = 3
    subscriber_kwargs: dict[str, Any] = {}

    @pytest.fixture()
    def raw_broker(self):
        return None

    def patch_broker(
        self, raw_broker: BrokerUsecase, broker: BrokerUsecase
    ) -> BrokerUsecase:
        return broker

    async def test_local_middleware(
        self,
        event: asyncio.Event,
        queue: str,
        mock: Mock,
        raw_broker,
    ):
        @asynccontextmanager
        async def mid(msg):
            mock.start(msg)
            yield msg
            mock.end()
            event.set()

        broker = self.broker_class()

        @broker.subscriber(queue, middlewares=(mid,), **self.subscriber_kwargs)
        async def handler(m):
            mock.inner(m)
            return "end"

        broker = self.patch_broker(raw_broker, broker)

        async with broker:
            await broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(broker.publish("start", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=self.timeout,
            )

        mock.start.assert_called_once_with("start")
        mock.inner.assert_called_once_with("start")

        assert event.is_set()
        mock.end.assert_called_once()

    async def test_publisher_middleware(
        self,
        event: asyncio.Event,
        queue: str,
        mock: Mock,
        raw_broker,
    ):
        @asynccontextmanager
        async def mid(msg, *args, **kwargs):
            mock.enter()
            yield msg
            mock.end()
            if mock.end.call_count > 1:
                event.set()

        broker = self.broker_class()

        @broker.subscriber(queue, **self.subscriber_kwargs)
        @broker.publisher(queue + "1", middlewares=(mid,))
        @broker.publisher(queue + "2", middlewares=(mid,))
        async def handler(m):
            mock.inner(m)
            return "end"

        broker = self.patch_broker(raw_broker, broker)

        async with broker:
            await broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(broker.publish("start", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=self.timeout,
            )

        assert event.is_set()
        mock.inner.assert_called_once_with("start")
        assert mock.enter.call_count == 2
        assert mock.end.call_count == 2

    async def test_local_middleware_not_shared_between_subscribers(
        self, queue: str, mock: Mock, raw_broker
    ):
        event1 = asyncio.Event()
        event2 = asyncio.Event()

        @asynccontextmanager
        async def mid(msg):
            mock.start(msg)
            yield msg
            mock.end()

        broker = self.broker_class()

        @broker.subscriber(queue, **self.subscriber_kwargs)
        @broker.subscriber(queue + "1", middlewares=(mid,), **self.subscriber_kwargs)
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
                timeout=self.timeout,
            )

        assert event1.is_set()
        assert event2.is_set()
        mock.start.assert_called_once()
        mock.end.assert_called_once()
        assert mock.call_count == 2

    async def test_local_middleware_consume_not_shared_between_filters(
        self, queue: str, mock: Mock, raw_broker
    ):
        event1 = asyncio.Event()
        event2 = asyncio.Event()

        @asynccontextmanager
        async def mid(msg):
            mock.start(msg)
            yield msg
            mock.end()

        broker = self.broker_class()

        @broker.subscriber(queue, filter=lambda m: m.content_type == "application/json", **self.subscriber_kwargs)
        async def handler(m):
            event2.set()
            mock()
            return ""

        @broker.subscriber(queue, middlewares=(mid,), **self.subscriber_kwargs)
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
                timeout=self.timeout,
            )

        assert event1.is_set()
        assert event2.is_set()
        mock.start.assert_called_once()
        mock.end.assert_called_once()
        assert mock.call_count == 2

    async def test_error_traceback(self, queue: str, mock: Mock, event, raw_broker):
        @asynccontextmanager
        async def mid(msg):
            try:
                yield msg
            except Exception as e:
                mock(isinstance(e, ValueError))

        broker = self.broker_class()

        @broker.subscriber(queue, middlewares=(mid,), **self.subscriber_kwargs)
        async def handler2(m):
            event.set()
            raise ValueError()

        broker = self.patch_broker(raw_broker, broker)

        async with broker:
            await broker.start()

            await asyncio.wait(
                (
                    asyncio.create_task(broker.publish("", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=self.timeout,
            )

        assert event.is_set()
        mock.assert_called_once_with(True)


@pytest.mark.asyncio()
class MiddlewareTestcase(LocalMiddlewareTestcase):
    async def test_global_middleware(
        self, event: asyncio.Event, queue: str, mock: Mock, raw_broker
    ):
        class mid(BaseMiddleware):  # noqa: N801
            async def on_receive(self):
                mock.start(self.msg)
                return await super().on_receive()

            async def after_processed(self, exc_type, exc_val, exc_tb):
                mock.end()
                return await super().after_processed(exc_type, exc_val, exc_tb)

        broker = self.broker_class(
            middlewares=(mid,),
        )

        @broker.subscriber(queue, **self.subscriber_kwargs)
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
                timeout=self.timeout,
            )

        assert event.is_set()
        mock.start.assert_called_once()
        mock.end.assert_called_once()

    async def test_patch_publish(self, queue: str, mock: Mock, event, raw_broker):
        class Mid(BaseMiddleware):
            async def on_publish(self, msg: str, *args, **kwargs) -> str:
                return msg * 2

        broker = self.broker_class(middlewares=(Mid,))

        @broker.subscriber(queue, **self.subscriber_kwargs)
        async def handler(m):
            return m

        @broker.subscriber(queue + "r", **self.subscriber_kwargs)
        async def handler_resp(m):
            mock(m)
            event.set()

        broker = self.patch_broker(raw_broker, broker)

        async with broker:
            await broker.start()

            await asyncio.wait(
                (
                    asyncio.create_task(
                        broker.publish("r", queue, reply_to=queue + "r")
                    ),
                    asyncio.create_task(event.wait()),
                ),
                timeout=self.timeout,
            )

        assert event.is_set()
        mock.assert_called_once_with("rrrr")

    async def test_global_publisher_middleware(
        self,
        event: asyncio.Event,
        queue: str,
        mock: Mock,
        raw_broker,
    ):
        class Mid(BaseMiddleware):
            async def on_publish(self, msg: str, *args, **kwargs) -> str:
                data = msg * 2
                assert args or kwargs
                mock.enter(data)
                return data

            async def after_publish(self, *args, **kwargs):
                mock.end()
                if mock.end.call_count > 2:
                    event.set()

        broker = self.broker_class(middlewares=(Mid,))

        @broker.subscriber(queue, **self.subscriber_kwargs)
        @broker.publisher(queue + "1")
        @broker.publisher(queue + "2")
        async def handler(m):
            mock.inner(m)
            return m

        broker = self.patch_broker(raw_broker, broker)

        async with broker:
            await broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(broker.publish("1", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=self.timeout,
            )

        assert event.is_set()
        mock.inner.assert_called_once_with("11")
        assert mock.enter.call_count == 3
        mock.enter.assert_called_with("1111")
        assert mock.end.call_count == 3
