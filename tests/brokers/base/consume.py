import asyncio
from typing import Any, ClassVar, Dict
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel

from faststream import Context, Depends
from faststream.broker.core.usecase import BrokerUsecase
from faststream.exceptions import StopConsume


@pytest.mark.asyncio()
class BrokerConsumeTestcase:
    timeout: int = 3
    subscriber_kwargs: ClassVar[Dict[str, Any]] = {}

    @pytest.fixture()
    def consume_broker(self, broker: BrokerUsecase):
        return broker

    async def test_consume(
        self,
        queue: str,
        consume_broker: BrokerUsecase,
        event: asyncio.Event,
    ):
        @consume_broker.subscriber(queue, **self.subscriber_kwargs)
        def subscriber(m):
            event.set()

        async with consume_broker:
            await consume_broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(consume_broker.publish("hello", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=self.timeout,
            )

        assert event.is_set()

    async def test_consume_from_multi(
        self,
        queue: str,
        consume_broker: BrokerUsecase,
        mock: MagicMock,
    ):
        consume = asyncio.Event()
        consume2 = asyncio.Event()

        @consume_broker.subscriber(queue, **self.subscriber_kwargs)
        @consume_broker.subscriber(queue + "1", **self.subscriber_kwargs)
        def subscriber(m):
            mock()
            if not consume.is_set():
                consume.set()
            else:
                consume2.set()

        async with consume_broker:
            await consume_broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(consume_broker.publish("hello", queue)),
                    asyncio.create_task(consume_broker.publish("hello", queue + "1")),
                    asyncio.create_task(consume.wait()),
                    asyncio.create_task(consume2.wait()),
                ),
                timeout=self.timeout,
            )

        assert consume2.is_set()
        assert consume.is_set()
        assert mock.call_count == 2

    async def test_consume_double(
        self,
        queue: str,
        consume_broker: BrokerUsecase,
        mock: MagicMock,
    ):
        consume = asyncio.Event()
        consume2 = asyncio.Event()

        @consume_broker.subscriber(queue, **self.subscriber_kwargs)
        async def handler(m):
            mock()
            if not consume.is_set():
                consume.set()
            else:
                consume2.set()

        async with consume_broker:
            await consume_broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(consume_broker.publish("hello", queue)),
                    asyncio.create_task(consume_broker.publish("hello", queue)),
                    asyncio.create_task(consume.wait()),
                    asyncio.create_task(consume2.wait()),
                ),
                timeout=self.timeout,
            )

        assert consume2.is_set()
        assert consume.is_set()
        assert mock.call_count == 2

    async def test_different_consume(
        self,
        queue: str,
        consume_broker: BrokerUsecase,
        mock: MagicMock,
    ):
        consume = asyncio.Event()
        consume2 = asyncio.Event()

        @consume_broker.subscriber(queue, **self.subscriber_kwargs)
        def handler(m):
            mock.handler()
            consume.set()

        another_topic = queue + "1"

        @consume_broker.subscriber(another_topic, **self.subscriber_kwargs)
        def handler2(m):
            mock.handler2()
            consume2.set()

        async with consume_broker:
            await consume_broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(consume_broker.publish("hello", queue)),
                    asyncio.create_task(consume_broker.publish("hello", another_topic)),
                    asyncio.create_task(consume.wait()),
                    asyncio.create_task(consume2.wait()),
                ),
                timeout=self.timeout,
            )

        assert consume.is_set()
        assert consume2.is_set()
        mock.handler.assert_called_once()
        mock.handler2.assert_called_once()

    async def test_consume_with_filter(
        self,
        queue: str,
        consume_broker: BrokerUsecase,
        mock: MagicMock,
    ):
        consume = asyncio.Event()
        consume2 = asyncio.Event()

        @consume_broker.subscriber(
            queue,
            filter=lambda m: m.content_type == "application/json",
            **self.subscriber_kwargs,
        )
        async def handler(m):
            mock.handler(m)
            consume.set()

        @consume_broker.subscriber(queue, **self.subscriber_kwargs)
        async def handler2(m):
            mock.handler2(m)
            consume2.set()

        async with consume_broker:
            await consume_broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(
                        consume_broker.publish({"msg": "hello"}, queue)
                    ),
                    asyncio.create_task(consume_broker.publish("hello", queue)),
                    asyncio.create_task(consume.wait()),
                    asyncio.create_task(consume2.wait()),
                ),
                timeout=self.timeout,
            )

        assert consume.is_set()
        assert consume2.is_set()
        mock.handler.assert_called_once_with({"msg": "hello"})
        mock.handler2.assert_called_once_with("hello")

    async def test_consume_validate_false(
        self,
        queue: str,
        consume_broker: BrokerUsecase,
        event: asyncio.Event,
        mock: MagicMock,
    ):
        consume_broker._is_apply_types = True
        consume_broker._is_validate = False

        class Foo(BaseModel):
            x: int

        def dependency() -> str:
            return "100"

        @consume_broker.subscriber(queue, **self.subscriber_kwargs)
        async def handler(m: Foo, dep: int = Depends(dependency), broker=Context()):
            mock(m, dep, broker)
            event.set()

        await consume_broker.start()
        await asyncio.wait(
            (
                asyncio.create_task(consume_broker.publish({"x": 1}, queue)),
                asyncio.create_task(event.wait()),
            ),
            timeout=self.timeout,
        )

        assert event.is_set()
        mock.assert_called_once_with({"x": 1}, "100", consume_broker)

    async def test_dynamic_sub(
        self,
        queue: str,
        consume_broker: BrokerUsecase,
        event: asyncio.Event,
    ):
        def subscriber(m):
            event.set()

        async with consume_broker:
            await consume_broker.start()

            sub = consume_broker.subscriber(queue, **self.subscriber_kwargs)
            sub(subscriber)
            consume_broker.setup_subscriber(sub)
            await sub.start()

            await asyncio.wait(
                (
                    asyncio.create_task(consume_broker.publish("hello", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=self.timeout,
            )

            await sub.close()

        assert event.is_set()


@pytest.mark.asyncio()
class BrokerRealConsumeTestcase(BrokerConsumeTestcase):
    @pytest.mark.slow()
    async def test_stop_consume_exc(
        self,
        queue: str,
        consume_broker: BrokerUsecase,
        event: asyncio.Event,
        mock: MagicMock,
    ):
        @consume_broker.subscriber(queue, **self.subscriber_kwargs)
        def subscriber(m):
            mock()
            event.set()
            raise StopConsume()

        async with consume_broker:
            await consume_broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(consume_broker.publish("hello", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=self.timeout,
            )
            await asyncio.sleep(0.5)
            await consume_broker.publish("hello", queue)
            await asyncio.sleep(0.5)

        assert event.is_set()
        mock.assert_called_once()
