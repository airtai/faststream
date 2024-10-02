import asyncio
from unittest.mock import Mock, call

import pytest

from faststream import Context
from faststream._internal.basic_types import DecodedMessage
from faststream.exceptions import SkipMessage
from faststream.middlewares import BaseMiddleware, ExceptionMiddleware

from .basic import BaseTestcaseConfig


@pytest.mark.asyncio
class LocalMiddlewareTestcase(BaseTestcaseConfig):
    async def test_subscriber_middleware(
        self,
        event: asyncio.Event,
        queue: str,
        mock: Mock,
    ):
        async def mid(call_next, msg):
            mock.start(await msg.decode())
            result = await call_next(msg)
            mock.end()
            event.set()
            return result

        broker = self.get_broker()

        args, kwargs = self.get_subscriber_params(queue, middlewares=(mid,))

        @broker.subscriber(*args, **kwargs)
        async def handler(m):
            mock.inner(m)
            return "end"

        async with self.patch_broker(broker) as br:
            await br.start()
            await asyncio.wait(
                (
                    asyncio.create_task(br.publish("start", queue)),
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
    ):
        async def mid(call_next, msg, **kwargs):
            mock.enter()
            result = await call_next(msg, **kwargs)
            mock.end()
            if mock.end.call_count > 1:
                event.set()
            return result

        broker = self.get_broker()

        args, kwargs = self.get_subscriber_params(queue)

        @broker.subscriber(*args, **kwargs)
        @broker.publisher(queue + "1", middlewares=(mid,))
        @broker.publisher(queue + "2", middlewares=(mid,))
        async def handler(m):
            mock.inner(m)
            return "end"

        async with self.patch_broker(broker) as br:
            await br.start()
            await asyncio.wait(
                (
                    asyncio.create_task(br.publish("start", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=self.timeout,
            )

        assert event.is_set()
        mock.inner.assert_called_once_with("start")
        assert mock.enter.call_count == 2
        assert mock.end.call_count == 2

    async def test_local_middleware_not_shared_between_subscribers(
        self,
        queue: str,
        mock: Mock,
    ):
        event1 = asyncio.Event()
        event2 = asyncio.Event()

        async def mid(call_next, msg):
            mock.start(msg)
            result = await call_next(msg)
            mock.end()
            return result

        broker = self.get_broker()

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

        async with self.patch_broker(broker) as br:
            await br.start()
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
        self,
        queue: str,
        mock: Mock,
    ):
        event1 = asyncio.Event()
        event2 = asyncio.Event()

        async def mid(call_next, msg):
            mock.start(msg)
            result = await call_next(msg)
            mock.end()
            return result

        broker = self.get_broker()

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

        async with self.patch_broker(broker) as br:
            await br.start()
            await asyncio.wait(
                (
                    asyncio.create_task(br.publish({"msg": "hi"}, queue)),
                    asyncio.create_task(br.publish("", queue)),
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

    async def test_error_traceback(self, queue: str, mock: Mock, event):
        async def mid(call_next, msg):
            try:
                result = await call_next(msg)
            except Exception as e:
                mock(isinstance(e, ValueError))
                raise e
            else:
                return result

        broker = self.get_broker()

        args, kwargs = self.get_subscriber_params(queue, middlewares=(mid,))

        @broker.subscriber(*args, **kwargs)
        async def handler2(m):
            event.set()
            raise ValueError

        async with self.patch_broker(broker) as br:
            await br.start()

            await asyncio.wait(
                (
                    asyncio.create_task(br.publish("", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=self.timeout,
            )

        assert event.is_set()
        mock.assert_called_once_with(True)


@pytest.mark.asyncio
class MiddlewareTestcase(LocalMiddlewareTestcase):
    async def test_global_middleware(
        self,
        event: asyncio.Event,
        queue: str,
        mock: Mock,
    ):
        class mid(BaseMiddleware):  # noqa: N801
            async def on_receive(self):
                mock.start(self.msg)
                return await super().on_receive()

            async def after_processed(self, exc_type, exc_val, exc_tb):
                mock.end()
                return await super().after_processed(exc_type, exc_val, exc_tb)

        broker = self.get_broker(
            middlewares=(mid,),
        )

        args, kwargs = self.get_subscriber_params(queue)

        @broker.subscriber(*args, **kwargs)
        async def handler(m):
            event.set()
            return ""

        async with self.patch_broker(broker) as br:
            await br.start()
            await asyncio.wait(
                (
                    asyncio.create_task(br.publish("", queue)),
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
    ):
        class mid(BaseMiddleware):  # noqa: N801
            async def on_receive(self):
                mock.start(self.msg)
                return await super().on_receive()

            async def after_processed(self, exc_type, exc_val, exc_tb):
                mock.end()
                return await super().after_processed(exc_type, exc_val, exc_tb)

        broker = self.get_broker()

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

        async with self.patch_broker(broker) as br:
            await br.start()
            await asyncio.wait(
                (
                    asyncio.create_task(br.publish("", queue)),
                    asyncio.create_task(br.publish("", f"{queue}1")),
                    asyncio.create_task(event.wait()),
                    asyncio.create_task(event2.wait()),
                ),
                timeout=self.timeout,
            )

        assert event.is_set()
        assert mock.start.call_count == 2
        assert mock.end.call_count == 2

    async def test_patch_publish(
        self,
        queue: str,
        mock: Mock,
        event: asyncio.Event,
    ):
        class Mid(BaseMiddleware):
            async def on_publish(self, msg: str, *args, **kwargs) -> str:
                return msg * 2

        broker = self.get_broker(middlewares=(Mid,))

        args, kwargs = self.get_subscriber_params(queue)

        @broker.subscriber(*args, **kwargs)
        async def handler(m):
            return m

        args2, kwargs2 = self.get_subscriber_params(queue + "r")

        @broker.subscriber(*args2, **kwargs2)
        async def handler_resp(m):
            mock(m)
            event.set()

        async with self.patch_broker(broker) as br:
            await br.start()

            await asyncio.wait(
                (
                    asyncio.create_task(br.publish("r", queue, reply_to=queue + "r")),
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

        broker = self.get_broker(middlewares=(Mid,))

        args, kwargs = self.get_subscriber_params(queue)

        @broker.subscriber(*args, **kwargs)
        @broker.publisher(queue + "1")
        @broker.publisher(queue + "2")
        async def handler(m):
            mock.inner(m)
            return m

        async with self.patch_broker(broker) as br:
            await br.start()
            await asyncio.wait(
                (
                    asyncio.create_task(br.publish("1", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=self.timeout,
            )

        assert event.is_set()
        mock.inner.assert_called_once_with("11")
        assert mock.enter.call_count == 3
        mock.enter.assert_called_with("1111")
        assert mock.end.call_count == 3


@pytest.mark.asyncio
class ExceptionMiddlewareTestcase(BaseTestcaseConfig):
    async def test_exception_middleware_default_msg(
        self,
        event: asyncio.Event,
        queue: str,
        mock: Mock,
    ):
        mid = ExceptionMiddleware()

        @mid.add_handler(ValueError, publish=True)
        async def value_error_handler(exc):
            return "value"

        broker = self.get_broker(apply_types=True, middlewares=(mid,))

        args, kwargs = self.get_subscriber_params(queue)

        @broker.subscriber(*args, **kwargs)
        @broker.publisher(queue + "1")
        async def subscriber1(m):
            raise ValueError

        args, kwargs = self.get_subscriber_params(queue + "1")

        @broker.subscriber(*args, **kwargs)
        async def subscriber2(msg=Context("message")):
            mock(await msg.decode())
            event.set()

        async with self.patch_broker(broker) as br:
            await br.start()
            await asyncio.wait(
                (
                    asyncio.create_task(br.publish("", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=self.timeout,
            )

        assert event.is_set()
        assert mock.call_count == 1
        mock.assert_called_once_with("value")

    async def test_exception_middleware_skip_msg(
        self,
        event: asyncio.Event,
        queue: str,
        mock: Mock,
    ):
        mid = ExceptionMiddleware()

        @mid.add_handler(ValueError, publish=True)
        async def value_error_handler(exc):
            event.set()
            raise SkipMessage()

        broker = self.get_broker(middlewares=(mid,))
        args, kwargs = self.get_subscriber_params(queue)

        @broker.subscriber(*args, **kwargs)
        @broker.publisher(queue + "1")
        async def subscriber1(m):
            raise ValueError

        args2, kwargs2 = self.get_subscriber_params(queue + "1")

        @broker.subscriber(*args2, **kwargs2)
        async def subscriber2(msg=Context("message")):
            mock(await msg.decode())

        async with self.patch_broker(broker) as br:
            await br.start()
            await asyncio.wait(
                (
                    asyncio.create_task(br.publish("", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=self.timeout,
            )

        assert event.is_set()
        assert mock.call_count == 0

    async def test_exception_middleware_do_not_catch_skip_msg(
        self,
        event: asyncio.Event,
        queue: str,
        mock: Mock,
    ):
        mid = ExceptionMiddleware()

        @mid.add_handler(Exception)
        async def value_error_handler(exc):
            mock()

        broker = self.get_broker(middlewares=(mid,))
        args, kwargs = self.get_subscriber_params(queue)

        @broker.subscriber(*args, **kwargs)
        async def subscriber(m):
            event.set()
            raise SkipMessage

        async with self.patch_broker(broker) as br:
            await br.start()
            await asyncio.wait(
                (
                    asyncio.create_task(br.publish("", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=self.timeout,
            )
            await asyncio.sleep(0.001)

        assert event.is_set()
        assert mock.call_count == 0

    async def test_exception_middleware_reraise(
        self,
        event: asyncio.Event,
        queue: str,
        mock: Mock,
    ):
        mid = ExceptionMiddleware()

        @mid.add_handler(ValueError, publish=True)
        async def value_error_handler(exc):
            event.set()
            raise exc

        broker = self.get_broker(middlewares=(mid,))
        args, kwargs = self.get_subscriber_params(queue)

        @broker.subscriber(*args, **kwargs)
        @broker.publisher(queue + "1")
        async def subscriber1(m):
            raise ValueError

        args2, kwargs2 = self.get_subscriber_params(queue + "1")

        @broker.subscriber(*args2, **kwargs2)
        async def subscriber2(msg=Context("message")):
            mock(await msg.decode())

        async with self.patch_broker(broker) as br:
            await br.start()
            await asyncio.wait(
                (
                    asyncio.create_task(br.publish("", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=self.timeout,
            )

        assert event.is_set()
        assert mock.call_count == 0

    async def test_exception_middleware_different_handler(
        self,
        event: asyncio.Event,
        queue: str,
        mock: Mock,
    ):
        mid = ExceptionMiddleware()

        @mid.add_handler(ZeroDivisionError, publish=True)
        async def zero_error_handler(exc):
            return "zero"

        @mid.add_handler(ValueError, publish=True)
        async def value_error_handler(exc):
            return "value"

        broker = self.get_broker(apply_types=True, middlewares=(mid,))
        args, kwargs = self.get_subscriber_params(queue)

        publisher = broker.publisher(queue + "2")

        @broker.subscriber(*args, **kwargs)
        @publisher
        async def subscriber1(m):
            raise ZeroDivisionError

        args2, kwargs2 = self.get_subscriber_params(queue + "1")

        @broker.subscriber(*args2, **kwargs2)
        @publisher
        async def subscriber2(m):
            raise ValueError

        args3, kwargs3 = self.get_subscriber_params(queue + "2")

        @broker.subscriber(*args3, **kwargs3)
        async def subscriber3(msg=Context("message")):
            mock(await msg.decode())
            if mock.call_count > 1:
                event.set()

        async with self.patch_broker(broker) as br:
            await br.start()
            await asyncio.wait(
                (
                    asyncio.create_task(br.publish("", queue)),
                    asyncio.create_task(br.publish("", queue + "1")),
                    asyncio.create_task(event.wait()),
                ),
                timeout=self.timeout,
            )

        assert event.is_set()
        assert mock.call_count == 2
        mock.assert_has_calls([call("zero"), call("value")], any_order=True)

    async def test_exception_middleware_init_handler_same(self):
        mid1 = ExceptionMiddleware()

        @mid1.add_handler(ValueError)
        async def value_error_handler(exc):
            return "value"

        mid2 = ExceptionMiddleware(handlers={ValueError: value_error_handler})

        assert [x[0] for x in mid1._handlers] == [x[0] for x in mid2._handlers]

    async def test_exception_middleware_init_publish_handler_same(self):
        mid1 = ExceptionMiddleware()

        @mid1.add_handler(ValueError, publish=True)
        async def value_error_handler(exc):
            return "value"

        mid2 = ExceptionMiddleware(publish_handlers={ValueError: value_error_handler})

        assert [x[0] for x in mid1._publish_handlers] == [
            x[0] for x in mid2._publish_handlers
        ]

    async def test_exception_middleware_decoder_error(
        self,
        event: asyncio.Event,
        queue: str,
        mock: Mock,
    ):
        async def decoder(
            msg,
            original_decoder,
        ) -> DecodedMessage:
            raise ValueError

        mid = ExceptionMiddleware()

        @mid.add_handler(ValueError)
        async def value_error_handler(exc):
            event.set()

        broker = self.get_broker(middlewares=(mid,), decoder=decoder)

        args, kwargs = self.get_subscriber_params(queue)

        @broker.subscriber(*args, **kwargs)
        async def subscriber1(m):
            raise ZeroDivisionError

        async with self.patch_broker(broker) as br:
            await br.start()
            await asyncio.wait(
                (
                    asyncio.create_task(br.publish("", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=self.timeout,
            )

        assert event.is_set()
