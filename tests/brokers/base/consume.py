import asyncio
from unittest.mock import Mock

import pytest

from faststream.broker.core.abc import BrokerUsecase
from faststream.exceptions import StopConsume


@pytest.mark.asyncio
class BrokerConsumeTestcase:
    @pytest.fixture
    def consume_broker(self, broker: BrokerUsecase):
        return broker

    async def test_consume(
        self,
        queue: str,
        consume_broker: BrokerUsecase,
        event: asyncio.Event,
    ):
        @consume_broker.subscriber(queue)
        def subscriber(m):
            event.set()

        await consume_broker.start()
        await asyncio.wait(
            (
                asyncio.create_task(consume_broker.publish("hello", queue)),
                asyncio.create_task(event.wait()),
            ),
            timeout=3,
        )

        assert event.is_set()

    async def test_consume_from_multi(
        self,
        mock: Mock,
        queue: str,
        consume_broker: BrokerUsecase,
    ):
        consume = asyncio.Event()
        consume2 = asyncio.Event()

        @consume_broker.subscriber(queue)
        @consume_broker.subscriber(queue + "1")
        def subscriber(m):
            if not consume.is_set():
                consume.set()
            else:
                consume2.set()
            mock()

        await consume_broker.start()
        await asyncio.wait(
            (
                asyncio.create_task(consume_broker.publish("hello", queue)),
                asyncio.create_task(consume_broker.publish("hello", queue + "1")),
                asyncio.create_task(consume.wait()),
                asyncio.create_task(consume2.wait()),
            ),
            timeout=3,
        )

        assert consume2.is_set()
        assert consume.is_set()
        assert mock.call_count == 2

    async def test_consume_double(
        self,
        mock: Mock,
        queue: str,
        consume_broker: BrokerUsecase,
    ):
        consume = asyncio.Event()
        consume2 = asyncio.Event()

        @consume_broker.subscriber(queue)
        async def handler(m):
            if not consume.is_set():
                consume.set()
            else:
                consume2.set()
            mock()

        await consume_broker.start()

        await asyncio.wait(
            (
                asyncio.create_task(consume_broker.publish("hello", queue)),
                asyncio.create_task(consume_broker.publish("hello", queue)),
                asyncio.create_task(consume.wait()),
                asyncio.create_task(consume2.wait()),
            ),
            timeout=3,
        )

        assert consume2.is_set()
        assert consume.is_set()
        assert mock.call_count == 2

    async def test_different_consume(
        self,
        mock: Mock,
        queue: str,
        consume_broker: BrokerUsecase,
    ):
        first_consume = asyncio.Event()
        second_consume = asyncio.Event()

        @consume_broker.subscriber(queue)
        def handler(m):
            first_consume.set()
            mock.method()

        another_topic = queue + "1"

        @consume_broker.subscriber(another_topic)
        def handler2(m):
            second_consume.set()
            mock.method2()

        await consume_broker.start()

        await asyncio.wait(
            (
                asyncio.create_task(consume_broker.publish("hello", queue)),
                asyncio.create_task(consume_broker.publish("hello", another_topic)),
                asyncio.create_task(first_consume.wait()),
                asyncio.create_task(second_consume.wait()),
            ),
            timeout=3,
        )

        assert first_consume.is_set()
        assert second_consume.is_set()
        mock.method.assert_called_once()
        mock.method2.assert_called_once()

    async def test_consume_with_filter(
        self,
        mock: Mock,
        queue: str,
        consume_broker: BrokerUsecase,
    ):
        consume = asyncio.Event()
        consume2 = asyncio.Event()

        @consume_broker.subscriber(
            queue, filter=lambda m: m.content_type == "application/json"
        )
        async def handler(m):
            consume2.set()
            mock.call1(m)

        @consume_broker.subscriber(queue)
        async def handler2(m):
            consume.set()
            mock.call2(m)

        await consume_broker.start()

        await asyncio.wait(
            (
                asyncio.create_task(consume_broker.publish({"msg": "hello"}, queue)),
                asyncio.create_task(consume_broker.publish("hello", queue)),
                asyncio.create_task(consume.wait()),
                asyncio.create_task(consume2.wait()),
            ),
            timeout=3,
        )

        assert consume2.is_set()
        assert consume.is_set()
        mock.call1.assert_called_once_with({"msg": "hello"})
        mock.call2.assert_called_once_with("hello")


@pytest.mark.asyncio
class BrokerRealConsumeTestcase(BrokerConsumeTestcase):
    @pytest.mark.slow
    async def test_stop_consume_exc(
        self,
        queue: str,
        mock: Mock,
        consume_broker: BrokerUsecase,
        event: asyncio.Event,
    ):
        @consume_broker.subscriber(queue)
        def subscriber(m):
            event.set()
            mock()
            raise StopConsume()

        await consume_broker.start()
        await asyncio.wait(
            (
                asyncio.create_task(consume_broker.publish("hello", queue)),
                asyncio.create_task(event.wait()),
            ),
            timeout=3,
        )
        await asyncio.sleep(0.5)
        await consume_broker.publish("hello", queue)
        await asyncio.sleep(0.5)

        assert event.is_set()
        mock.assert_called_once()
