import asyncio
from unittest.mock import MagicMock

import pytest

from faststream.redis import ListSub, RedisBroker
from tests.brokers.base.publish import BrokerPublishTestcase


@pytest.mark.redis()
@pytest.mark.asyncio()
class TestPublish(BrokerPublishTestcase):  # noqa: D101
    async def test_list_publisher(
        self,
        queue: str,
        pub_broker: RedisBroker,
        event: asyncio.Event,
        mock: MagicMock,
    ):
        @pub_broker.subscriber(list=queue)
        @pub_broker.publisher(list=queue + "resp")
        async def m():
            return ""

        @pub_broker.subscriber(list=queue + "resp")
        async def resp(msg):
            event.set()
            mock(msg)

        async with pub_broker:
            await pub_broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(pub_broker.publish("", list=queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        assert event.is_set()
        mock.assert_called_once_with("")

    async def test_list_publish_batch(self, queue: str, broker: RedisBroker):
        msgs_queue = asyncio.Queue(maxsize=2)

        @broker.subscriber(list=queue)
        async def handler(msg):
            await msgs_queue.put(msg)

        async with broker:
            await broker.start()

            await broker.publish_batch(1, "hi", list=queue)

            result, _ = await asyncio.wait(
                (
                    asyncio.create_task(msgs_queue.get()),
                    asyncio.create_task(msgs_queue.get()),
                ),
                timeout=3,
            )

        assert {1, b"hi"} == {r.result() for r in result}

    async def test_batch_list_publisher(
        self,
        queue: str,
        pub_broker: RedisBroker,
        event: asyncio.Event,
        mock: MagicMock,
    ):
        batch_list = ListSub(queue + "resp", batch=True)

        @pub_broker.subscriber(list=queue)
        @pub_broker.publisher(list=batch_list)
        async def m():
            return 1, 2, 3

        @pub_broker.subscriber(list=batch_list)
        async def resp(msg):
            event.set()
            mock(msg)

        async with pub_broker:
            await pub_broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(pub_broker.publish("", list=queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        assert event.is_set()
        mock.assert_called_once_with([1, 2, 3])
