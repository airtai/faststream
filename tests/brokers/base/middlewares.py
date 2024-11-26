import asyncio
from typing import Type
from unittest.mock import Mock, call

import pytest

from faststream import Context
from faststream.broker.core.usecase import BrokerUsecase
from faststream.broker.middlewares import BaseMiddleware, ExceptionMiddleware
from faststream.exceptions import SkipMessage
from faststream.types import DecodedMessage

from .basic import BaseTestcaseConfig


@pytest.mark.asyncio
class MiddlewaresOrderTestcase(BaseTestcaseConfig):
    broker_class: Type[BrokerUsecase]

    @pytest.fixture
    def raw_broker(self):
        return None

    def patch_broker(
        self, raw_broker: BrokerUsecase, broker: BrokerUsecase
    ) -> BrokerUsecase:
        return broker

    async def test_broker_middleware_order(self, queue: str, mock: Mock, raw_broker):
        class InnerMiddleware(BaseMiddleware):
            async def consume_scope(self, call_next, msg):
                mock.consume_inner()
                mock.sub("inner")
                return await call_next(msg)

            async def publish_scope(self, call_next, msg, *args, **kwargs):
                mock.publish_inner()
                mock.pub("inner")
                return await call_next(msg, *args, **kwargs)

        class OuterMiddleware(BaseMiddleware):
            async def consume_scope(self, call_next, msg):
                mock.consume_outer()
                mock.sub("outer")
                return await call_next(msg)

            async def publish_scope(self, call_next, msg, *args, **kwargs):
                mock.publish_outer()
                mock.pub("outer")
                return await call_next(msg, *args, **kwargs)

        broker = self.broker_class(middlewares=[OuterMiddleware, InnerMiddleware])

        args, kwargs = self.get_subscriber_params(queue)

        @broker.subscriber(*args, **kwargs)
        async def handler(msg):
            pass

        async with self.patch_broker(raw_broker, broker) as br:
            await br.publish(None, queue)

        mock.consume_inner.assert_called_once()
        mock.consume_outer.assert_called_once()
        mock.publish_inner.assert_called_once()
        mock.publish_outer.assert_called_once()

        assert [c.args[0] for c in mock.sub.call_args_list] == ["outer", "inner"]
        assert [c.args[0] for c in mock.pub.call_args_list] == ["outer", "inner"]

    async def test_publisher_middleware_order(self, queue: str, mock: Mock, raw_broker):
        class InnerMiddleware(BaseMiddleware):
            async def publish_scope(self, call_next, msg, *args, **kwargs):
                mock.publish_inner()
                mock("inner")
                return await call_next(msg, *args, **kwargs)

        class MiddleMiddleware(BaseMiddleware):
            async def publish_scope(self, call_next, msg, *args, **kwargs):
                mock.publish_middle()
                mock("middle")
                return await call_next(msg, *args, **kwargs)

        class OuterMiddleware(BaseMiddleware):
            async def publish_scope(self, call_next, msg, *args, **kwargs):
                mock.publish_outer()
                mock("outer")
                return await call_next(msg, *args, **kwargs)

        broker = self.broker_class(middlewares=[OuterMiddleware])
        publisher = broker.publisher(
            queue,
            middlewares=[
                MiddleMiddleware(None).publish_scope,
                InnerMiddleware(None).publish_scope,
            ],
        )

        args, kwargs = self.get_subscriber_params(queue)

        @broker.subscriber(*args, **kwargs)
        async def handler(msg):
            pass

        async with self.patch_broker(raw_broker, broker):
            await publisher.publish(None, queue)

        mock.publish_inner.assert_called_once()
        mock.publish_middle.assert_called_once()
        mock.publish_outer.assert_called_once()

        assert [c.args[0] for c in mock.call_args_list] == ["outer", "middle", "inner"]

    async def test_publisher_with_router_middleware_order(self, queue: str, mock: Mock, raw_broker):
        class InnerMiddleware(BaseMiddleware):
            async def publish_scope(self, call_next, msg, *args, **kwargs):
                mock.publish_inner()
                mock("inner")
                return await call_next(msg, *args, **kwargs)

        class MiddleMiddleware(BaseMiddleware):
            async def publish_scope(self, call_next, msg, *args, **kwargs):
                mock.publish_middle()
                mock("middle")
                return await call_next(msg, *args, **kwargs)

        class OuterMiddleware(BaseMiddleware):
            async def publish_scope(self, call_next, msg, *args, **kwargs):
                mock.publish_outer()
                mock("outer")
                return await call_next(msg, *args, **kwargs)

        broker = self.broker_class(middlewares=[OuterMiddleware])
        router = self.broker_class(middlewares=[MiddleMiddleware])
        router2 = self.broker_class(middlewares=[InnerMiddleware])

        publisher = router2.publisher(queue)

        args, kwargs = self.get_subscriber_params(queue)

        @router2.subscriber(*args, **kwargs)
        async def handler(msg):
            pass

        router.include_router(router2)
        broker.include_router(router)

        async with self.patch_broker(raw_broker, broker):
            await publisher.publish(None, queue)

        mock.publish_inner.assert_called_once()
        mock.publish_middle.assert_called_once()
        mock.publish_outer.assert_called_once()

        assert [c.args[0] for c in mock.call_args_list] == ["outer", "middle", "inner"]

    async def test_consume_middleware_order(self, queue: str, mock: Mock, raw_broker):
        class InnerMiddleware(BaseMiddleware):
            async def consume_scope(self, call_next, msg):
                mock.consume_inner()
                mock("inner")
                return await call_next(msg)

        class MiddleMiddleware(BaseMiddleware):
            async def consume_scope(self, call_next, msg):
                mock.consume_middle()
                mock("middle")
                return await call_next(msg)

        class OuterMiddleware(BaseMiddleware):
            async def consume_scope(self, call_next, msg):
                mock.consume_outer()
                mock("outer")
                return await call_next(msg)

        broker = self.broker_class(middlewares=[OuterMiddleware])

        args, kwargs = self.get_subscriber_params(
            queue,
            middlewares=[
                MiddleMiddleware(None).consume_scope,
                InnerMiddleware(None).consume_scope,
            ],
        )

        @broker.subscriber(*args, **kwargs)
        async def handler(msg):
            pass

        async with self.patch_broker(raw_broker, broker) as br:
            await br.publish(None, queue)

        mock.consume_inner.assert_called_once()
        mock.consume_middle.assert_called_once()
        mock.consume_outer.assert_called_once()

        assert [c.args[0] for c in mock.call_args_list] == ["outer", "middle", "inner"]

    async def test_consume_with_middleware_order(self, queue: str, mock: Mock, raw_broker):
        class InnerMiddleware(BaseMiddleware):
            async def consume_scope(self, call_next, msg):
                mock.consume_inner()
                mock("inner")
                return await call_next(msg)

        class MiddleMiddleware(BaseMiddleware):
            async def consume_scope(self, call_next, msg):
                mock.consume_middle()
                mock("middle")
                return await call_next(msg)

        class OuterMiddleware(BaseMiddleware):
            async def consume_scope(self, call_next, msg):
                mock.consume_outer()
                mock("outer")
                return await call_next(msg)

        broker = self.broker_class(middlewares=[OuterMiddleware])
        router = self.broker_class(middlewares=[MiddleMiddleware])
        router2 = self.broker_class(middlewares=[InnerMiddleware])

        args, kwargs = self.get_subscriber_params(queue)

        @router2.subscriber(*args, **kwargs)
        async def handler(msg):
            pass

        router.include_router(router2)
        broker.include_router(router)
        async with self.patch_broker(raw_broker, broker) as br:
            await br.publish(None, queue)

        mock.consume_inner.assert_called_once()
        mock.consume_middle.assert_called_once()
        mock.consume_outer.assert_called_once()

        assert [c.args[0] for c in mock.call_args_list] == ["outer", "middle", "inner"]

    async def test_aenter_aexit(self, queue: str, mock: Mock, raw_broker):
        class InnerMiddleware(BaseMiddleware):
            async def __aenter__(self):
                mock.enter_inner()
                mock.enter("inner")
                return self

            async def __aexit__(
                self,
                exc_type=None,
                exc_val=None,
                exc_tb=None,
            ):
                mock.exit_inner()
                mock.exit("inner")
                return await self.after_processed(exc_type, exc_val, exc_tb)

        class OuterMiddleware(BaseMiddleware):
            async def __aenter__(self):
                mock.enter_outer()
                mock.enter("outer")
                return self

            async def __aexit__(
                self,
                exc_type=None,
                exc_val=None,
                exc_tb=None,
            ):
                mock.exit_outer()
                mock.exit("outer")
                return await self.after_processed(exc_type, exc_val, exc_tb)

        broker = self.broker_class(middlewares=[OuterMiddleware, InnerMiddleware])

        args, kwargs = self.get_subscriber_params(queue)

        @broker.subscriber(*args, **kwargs)
        async def handler_sub(msg):
            pass

        async with self.patch_broker(raw_broker, broker) as br:
            await br.publish(None, queue)

        mock.enter_inner.assert_called_once()
        mock.enter_outer.assert_called_once()
        mock.exit_inner.assert_called_once()
        mock.exit_outer.assert_called_once()

        assert [c.args[0] for c in mock.enter.call_args_list] == ["outer", "inner"]
        assert [c.args[0] for c in mock.exit.call_args_list] == ["inner", "outer"]


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
            mock.start(await msg.decode())
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


@pytest.mark.asyncio
class ExceptionMiddlewareTestcase(BaseTestcaseConfig):
    broker_class: Type[BrokerUsecase]

    @pytest.fixture
    def raw_broker(self):
        return None

    def patch_broker(
        self, raw_broker: BrokerUsecase, broker: BrokerUsecase
    ) -> BrokerUsecase:
        return broker

    async def test_exception_middleware_default_msg(
        self, event: asyncio.Event, queue: str, mock: Mock, raw_broker
    ):
        mid = ExceptionMiddleware()

        @mid.add_handler(ValueError, publish=True)
        async def value_error_handler(exc):
            return "value"

        broker = self.broker_class(middlewares=(mid,))

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
        assert mock.call_count == 1
        mock.assert_called_once_with("value")

    async def test_exception_middleware_skip_msg(
        self, event: asyncio.Event, queue: str, mock: Mock, raw_broker
    ):
        mid = ExceptionMiddleware()

        @mid.add_handler(ValueError, publish=True)
        async def value_error_handler(exc):
            event.set()
            raise SkipMessage()

        broker = self.broker_class(middlewares=(mid,))
        args, kwargs = self.get_subscriber_params(queue)

        @broker.subscriber(*args, **kwargs)
        @broker.publisher(queue + "1")
        async def subscriber1(m):
            raise ValueError

        args2, kwargs2 = self.get_subscriber_params(queue + "1")

        @broker.subscriber(*args2, **kwargs2)
        async def subscriber2(msg=Context("message")):
            mock(await msg.decode())

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
        assert mock.call_count == 0

    async def test_exception_middleware_do_not_catch_skip_msg(
        self, event: asyncio.Event, queue: str, mock: Mock, raw_broker
    ):
        mid = ExceptionMiddleware()

        @mid.add_handler(Exception)
        async def value_error_handler(exc):
            mock()

        broker = self.broker_class(middlewares=(mid,))
        args, kwargs = self.get_subscriber_params(queue)

        @broker.subscriber(*args, **kwargs)
        async def subscriber(m):
            event.set()
            raise SkipMessage

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
            await asyncio.sleep(0.001)

        assert event.is_set()
        assert mock.call_count == 0

    async def test_exception_middleware_reraise(
        self, event: asyncio.Event, queue: str, mock: Mock, raw_broker
    ):
        mid = ExceptionMiddleware()

        @mid.add_handler(ValueError, publish=True)
        async def value_error_handler(exc):
            event.set()
            raise exc

        broker = self.broker_class(middlewares=(mid,))
        args, kwargs = self.get_subscriber_params(queue)

        @broker.subscriber(*args, **kwargs)
        @broker.publisher(queue + "1")
        async def subscriber1(m):
            raise ValueError

        args2, kwargs2 = self.get_subscriber_params(queue + "1")

        @broker.subscriber(*args2, **kwargs2)
        async def subscriber2(msg=Context("message")):
            mock(await msg.decode())

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
        assert mock.call_count == 0

    async def test_exception_middleware_different_handler(
        self, event: asyncio.Event, queue: str, mock: Mock, raw_broker
    ):
        mid = ExceptionMiddleware()

        @mid.add_handler(ZeroDivisionError, publish=True)
        async def zero_error_handler(exc):
            return "zero"

        @mid.add_handler(ValueError, publish=True)
        async def value_error_handler(exc):
            return "value"

        broker = self.broker_class(middlewares=(mid,))
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

        broker = self.patch_broker(raw_broker, broker)

        async with broker:
            await broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(broker.publish("", queue)),
                    asyncio.create_task(broker.publish("", queue + "1")),
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
        self, event: asyncio.Event, queue: str, mock: Mock, raw_broker
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

        broker = self.broker_class(middlewares=(mid,), decoder=decoder)

        args, kwargs = self.get_subscriber_params(queue)

        @broker.subscriber(*args, **kwargs)
        async def subscriber1(m):
            raise ZeroDivisionError

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
