import asyncio
from unittest.mock import MagicMock, patch

import pytest
from redis.asyncio import Redis

from faststream.redis import ListSub, RedisBroker, StreamSub
from tests.brokers.base.publish import BrokerPublishTestcase
from tests.tools import spy_decorator


@pytest.mark.redis()
@pytest.mark.asyncio()
class TestPublish(BrokerPublishTestcase):
    @pytest.fixture()
    def pub_broker(self):
        return RedisBroker()

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

    async def test_list_publish_batch(self, queue: str, pub_broker: RedisBroker):
        msgs_queue = asyncio.Queue(maxsize=2)

        @pub_broker.subscriber(list=queue)
        async def handler(msg):
            await msgs_queue.put(msg)

        async with pub_broker:
            await pub_broker.start()

            await pub_broker.publish_batch(1, "hi", list=queue)

            result, _ = await asyncio.wait(
                (
                    asyncio.create_task(msgs_queue.get()),
                    asyncio.create_task(msgs_queue.get()),
                ),
                timeout=3,
            )

        assert {1, "hi"} == {r.result() for r in result}

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

    async def test_publisher_with_maxlen(
        self,
        queue: str,
        pub_broker: RedisBroker,
        event: asyncio.Event,
        mock: MagicMock,
    ):
        stream = StreamSub(queue + "resp", maxlen=1)

        @pub_broker.subscriber(stream=queue)
        @pub_broker.publisher(stream=stream)
        async def handler(msg):
            return msg

        @pub_broker.subscriber(stream=stream)
        async def resp(msg):
            event.set()
            mock(msg)

        with patch.object(Redis, "xadd", spy_decorator(Redis.xadd)) as m:
            async with pub_broker:
                await pub_broker.start()
                await asyncio.wait(
                    (
                        asyncio.create_task(pub_broker.publish("hi", stream=queue)),
                        asyncio.create_task(event.wait()),
                    ),
                    timeout=3,
                )

        assert event.is_set()
        mock.assert_called_once_with("hi")

        assert m.mock.call_args_list[-1].kwargs["maxlen"] == 1
