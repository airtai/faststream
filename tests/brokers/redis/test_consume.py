import asyncio
from unittest.mock import MagicMock

import pytest

from faststream.redis import ListSub, PubSub, RedisBroker
from tests.brokers.base.consume import BrokerRealConsumeTestcase


@pytest.mark.redis
@pytest.mark.asyncio
class TestConsume(BrokerRealConsumeTestcase):
    async def test_consume_batch(self, queue: str, broker: RedisBroker):
        msgs_queue = asyncio.Queue(maxsize=1)

        @broker.subscriber(list=ListSub(queue, batch=True))
        async def handler(msg):
            await msgs_queue.put(msg)

        async with broker:
            await broker.start()

            await broker.publish_batch(1, "hi", list=queue)

            result, _ = await asyncio.wait(
                (asyncio.create_task(msgs_queue.get()),),
                timeout=3,
            )

        assert [{"1", "hi"}] == [set(r.result()) for r in result]

    async def test_pattern_with_path(
        self,
        consume_broker: RedisBroker,
        event: asyncio.Event,
        mock: MagicMock,
    ):
        @consume_broker.subscriber("test.{name}")
        async def handler(msg):
            mock(msg)
            event.set()

        async with consume_broker:
            await consume_broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(consume_broker.publish("hello", "test.name")),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        mock.assert_called_once_with("hello")

    async def test_consume_list(
        self,
        consume_broker: RedisBroker,
        event: asyncio.Event,
        queue: str,
        mock: MagicMock,
    ):
        @consume_broker.subscriber(list=queue)
        async def handler(msg):
            mock(msg)
            event.set()

        async with consume_broker:
            await consume_broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(consume_broker.publish("hello", list=queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        mock.assert_called_once_with("hello")

    async def test_pattern_without_path(
        self,
        consume_broker: RedisBroker,
        event: asyncio.Event,
        mock: MagicMock,
    ):
        @consume_broker.subscriber(PubSub("test.*", pattern=True))
        async def handler(msg):
            mock(msg)
            event.set()

        async with consume_broker:
            await consume_broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(consume_broker.publish("hello", "test.name")),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        mock.assert_called_once_with("hello")
