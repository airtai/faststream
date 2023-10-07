import asyncio
from typing import Type
from unittest.mock import Mock

import pytest

from faststream.broker.core.abc import BrokerUsecase
from faststream.broker.middlewares import BaseMiddleware


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
        class mid(BaseMiddleware):
            async def on_receive(self):
                mock.start(self.msg)
                return await super().on_receive()

            async def after_processed(self, exc_type, exc_val, exec_tb):
                mock.end()
                return await super().after_processed(exc_type, exc_val, exec_tb)

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

        class mid(BaseMiddleware):
            async def on_receive(self):
                mock.start(self.msg)
                return await super().on_receive()

            async def after_processed(self, exc_type, exc_val, exec_tb):
                mock.end()
                return await super().after_processed(exc_type, exc_val, exec_tb)

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

    async def test_local_middleware_consume_not_shared_between_filters(
        self, queue: str, mock: Mock, raw_broker
    ):
        event1 = asyncio.Event()
        event2 = asyncio.Event()

        class mid(BaseMiddleware):
            async def on_consume(self, msg):
                mock.start(msg)
                return await super().on_consume(msg)

            async def after_consume(self, err):
                mock.end()
                return await super().after_consume(err)

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

    async def test_error_traceback(self, queue: str, mock: Mock, event, raw_broker):
        class Mid(BaseMiddleware):
            async def after_processed(self, exc_type, exc_val, exec_tb) -> bool:
                mock(issubclass(exc_type, ValueError))
                return True

            async def after_consume(self, err: Exception) -> None:
                mock(isinstance(err, ValueError))
                return await super().after_consume(err)

        broker = self.broker_class()

        @broker.subscriber(queue, middlewares=(Mid,))
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
                timeout=3,
            )

        assert event.is_set()
        assert mock.call_count == 2
        mock.assert_called_with(True)

    async def test_patch_publish(self, queue: str, mock: Mock, event, raw_broker):
        class Mid(BaseMiddleware):
            async def on_publish(self, msg: str) -> str:
                return msg * 2

        broker = self.broker_class()

        @broker.subscriber(queue, middlewares=(Mid, Mid))
        async def handler(m):
            return "r"

        @broker.subscriber(queue + "r")
        async def handler_resp(m):
            mock(m)
            event.set()

        broker = self.patch_broker(raw_broker, broker)

        async with broker:
            await broker.start()

            await asyncio.wait(
                (
                    asyncio.create_task(
                        broker.publish("", queue, reply_to=queue + "r")
                    ),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        assert event.is_set()
        mock.assert_called_once_with("rrrr")


@pytest.mark.asyncio
class MiddlewareTestcase(LocalMiddlewareTestcase):
    async def test_global_middleware(
        self, event: asyncio.Event, queue: str, mock: Mock, raw_broker
    ):
        class mid(BaseMiddleware):
            async def on_receive(self):
                mock.start(self.msg)
                return await super().on_receive()

            async def after_processed(self, exc_type, exc_val, exec_tb):
                mock.end()
                return await super().after_processed(exc_type, exc_val, exec_tb)

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
