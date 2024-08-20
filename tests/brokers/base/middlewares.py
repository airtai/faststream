import asyncio
from typing import Type
from unittest.mock import Mock

import pytest

from faststream.broker.core.usecase import BrokerUsecase
from faststream.broker.middlewares import BaseMiddleware

from .basic import BaseTestcaseConfig


@pytest.mark.asyncio
class LocalMiddlewareTestcase(BaseTestcaseConfig):
    broker_class: Type[BrokerUsecase]

    @pytest.fixture
    def raw_broker(self):
        return None

    def patch_broker(
        self, raw_broker: BrokerUsecase, broker: BrokerUsecase
    ) -> BrokerUsecase:
        return broker

    async def test_subscriber_middleware(
        self,
        event: asyncio.Event,
        queue: str,
        mock: Mock,
        raw_broker,
    ):
        async def mid(call_next, msg):
            mock.start(msg.decoded_body)
            result = await call_next(msg)
            mock.end()
            event.set()
            return result

        broker = self.broker_class()

        args, kwargs = self.get_subscriber_params(queue, middlewares=(mid,))

        @broker.subscriber(*args, **kwargs)
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
        async def mid(call_next, msg, **kwargs):
            mock.enter()
            result = await call_next(msg, **kwargs)
            mock.end()
            if mock.end.call_count > 1:
                event.set()
            return result

        broker = self.broker_class()

        args, kwargs = self.get_subscriber_params(queue)

        @broker.subscriber(*args, **kwargs)
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

        async def mid(call_next, msg):
            mock.start(msg)
            result = await call_next(msg)
            mock.end()
            return result

        broker = self.broker_class()

        args, kwargs = self.get_subscriber_params(queue)
        args2, kwargs2 = self.get_subscriber_params(
            queue + "1",
            middlewares=(mid,),
        )

        @broker.subscriber(*args, **kwargs)
        @broker.subscriber(*args2, **kwargs2)
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

        async def mid(call_next, msg):
            mock.start(msg)
            result = await call_next(msg)
            mock.end()
            return result

        broker = self.broker_class()

        args, kwargs = self.get_subscriber_params(
            queue,
        )

        sub = broker.subscriber(*args, **kwargs)

        @sub(filter=lambda m: m.content_type == "application/json")
        async def handler(m):
            event2.set()
            mock()
            return ""

        @sub(middlewares=(mid,))
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
        async def mid(call_next, msg):
            try:
                result = await call_next(msg)
            except Exception as e:
                mock(isinstance(e, ValueError))
                raise e
            else:
                return result

        broker = self.broker_class()

        args, kwargs = self.get_subscriber_params(queue, middlewares=(mid,))

        @broker.subscriber(*args, **kwargs)
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


@pytest.mark.asyncio
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

        args, kwargs = self.get_subscriber_params(queue)

        @broker.subscriber(*args, **kwargs)
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

    async def test_add_global_middleware(
        self,
        event: asyncio.Event,
        queue: str,
        mock: Mock,
        raw_broker,
    ):
        class mid(BaseMiddleware):  # noqa: N801
            async def on_receive(self):
                mock.start(self.msg)
                return await super().on_receive()

            async def after_processed(self, exc_type, exc_val, exc_tb):
                mock.end()
                return await super().after_processed(exc_type, exc_val, exc_tb)

        broker = self.broker_class()

        # already registered subscriber
        args, kwargs = self.get_subscriber_params(queue)

        @broker.subscriber(*args, **kwargs)
        async def handler(m):
            event.set()
            return ""

        # should affect to already registered and a new subscriber both
        broker.add_middleware(mid)

        event2 = asyncio.Event()

        # new subscriber
        args2, kwargs2 = self.get_subscriber_params(queue + "1")

        @broker.subscriber(*args2, **kwargs2)
        async def handler2(m):
            event2.set()
            return ""

        broker = self.patch_broker(raw_broker, broker)

        async with broker:
            await broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(broker.publish("", queue)),
                    asyncio.create_task(broker.publish("", f"{queue}1")),
                    asyncio.create_task(event.wait()),
                    asyncio.create_task(event2.wait()),
                ),
                timeout=self.timeout,
            )

        assert event.is_set()
        assert mock.start.call_count == 2
        assert mock.end.call_count == 2

    async def test_patch_publish(self, queue: str, mock: Mock, event, raw_broker):
        class Mid(BaseMiddleware):
            async def on_publish(self, msg: str, *args, **kwargs) -> str:
                return msg * 2

        broker = self.broker_class(middlewares=(Mid,))

        args, kwargs = self.get_subscriber_params(queue)

        @broker.subscriber(*args, **kwargs)
        async def handler(m):
            return m

        args2, kwargs2 = self.get_subscriber_params(queue + "r")

        @broker.subscriber(*args2, **kwargs2)
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

        args, kwargs = self.get_subscriber_params(queue)

        @broker.subscriber(*args, **kwargs)
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
