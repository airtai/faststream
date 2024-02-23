import asyncio
from unittest.mock import MagicMock, patch

import pytest
from redis.asyncio import Redis

from faststream.redis import ListSub, PubSub, RedisBroker, RedisMessage, StreamSub
from tests.brokers.base.consume import BrokerRealConsumeTestcase
from tests.tools import spy_decorator


@pytest.mark.redis()
@pytest.mark.asyncio()
class TestConsume(BrokerRealConsumeTestcase):  # noqa: D101
    async def test_consume_native(
        self,
        consume_broker: RedisBroker,
        event: asyncio.Event,
        mock: MagicMock,
        queue: str,
    ):
        @consume_broker.subscriber(queue)
        async def handler(msg):
            mock(msg)
            event.set()

        async with consume_broker:
            await consume_broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(
                        consume_broker._connection.publish(queue, "hello")
                    ),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        mock.assert_called_once_with(b"hello")

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


@pytest.mark.redis()
@pytest.mark.asyncio()
class TestConsumeList:  # noqa: D101
    async def test_consume_list(
        self,
        broker: RedisBroker,
        event: asyncio.Event,
        queue: str,
        mock: MagicMock,
    ):
        @broker.subscriber(list=queue)
        async def handler(msg):
            mock(msg)
            event.set()

        async with broker:
            await broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(broker.publish("hello", list=queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        mock.assert_called_once_with("hello")

    async def test_consume_list_native(
        self,
        broker: RedisBroker,
        event: asyncio.Event,
        queue: str,
        mock: MagicMock,
    ):
        @broker.subscriber(list=queue)
        async def handler(msg):
            mock(msg)
            event.set()

        async with broker:
            await broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(broker._connection.rpush(queue, "hello")),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        mock.assert_called_once_with(b"hello")

    @pytest.mark.slow()
    async def test_consume_list_batch_with_one(self, queue: str, broker: RedisBroker):
        msgs_queue = asyncio.Queue(maxsize=1)

        @broker.subscriber(list=ListSub(queue, batch=True, polling_interval=1))
        async def handler(msg):
            await msgs_queue.put(msg)

        async with broker:
            await broker.start()

            await broker.publish("hi", list=queue)

            result, _ = await asyncio.wait(
                (asyncio.create_task(msgs_queue.get()),),
                timeout=3,
            )

        assert ["hi"] == [r.result()[0] for r in result]

    @pytest.mark.slow()
    async def test_consume_list_batch(self, queue: str, broker: RedisBroker):
        msgs_queue = asyncio.Queue(maxsize=1)

        @broker.subscriber(list=ListSub(queue, batch=True, polling_interval=1))
        async def handler(msg):
            await msgs_queue.put(msg)

        async with broker:
            await broker.start()

            await broker.publish_batch(1, "hi", list=queue)

            result, _ = await asyncio.wait(
                (asyncio.create_task(msgs_queue.get()),),
                timeout=3,
            )

        assert [{1, "hi"}] == [set(r.result()) for r in result]

    @pytest.mark.slow()
    async def test_consume_list_batch_native(self, queue: str, broker: RedisBroker):
        msgs_queue = asyncio.Queue(maxsize=1)

        @broker.subscriber(list=ListSub(queue, batch=True, polling_interval=1))
        async def handler(msg):
            await msgs_queue.put(msg)

        async with broker:
            await broker.start()

            await broker._connection.rpush(queue, 1, "hi")

            result, _ = await asyncio.wait(
                (asyncio.create_task(msgs_queue.get()),),
                timeout=3,
            )

        assert [{1, "hi"}] == [set(r.result()) for r in result]


@pytest.mark.redis()
@pytest.mark.asyncio()
class TestConsumeStream:  # noqa: D101
    async def test_consume_stream(
        self,
        broker: RedisBroker,
        event: asyncio.Event,
        mock: MagicMock,
        queue,
    ):
        @broker.subscriber(stream=StreamSub(queue, polling_interval=3000))
        async def handler(msg):
            mock(msg)
            event.set()

        async with broker:
            await broker.start()

            await asyncio.wait(
                (
                    asyncio.create_task(broker.publish("hello", stream=queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        mock.assert_called_once_with("hello")

    @pytest.mark.asyncio()
    async def test_consume_group(
        self,
        queue: str,
        full_broker: RedisBroker,
    ):
        @full_broker.subscriber(stream=StreamSub(queue, group="group", consumer=queue))
        async def handler(msg: RedisMessage):
            ...

        assert next(iter(full_broker.handlers.values())).last_id == ">"

    @pytest.mark.asyncio()
    async def test_consume_group_with_last_id(
        self,
        queue: str,
        full_broker: RedisBroker,
    ):
        @full_broker.subscriber(stream=StreamSub(queue, group="group", consumer=queue, last_id="1"))
        async def handler(msg: RedisMessage):
            ...

        assert next(iter(full_broker.handlers.values())).last_id == "1"

    async def test_consume_stream_native(
        self,
        broker: RedisBroker,
        event: asyncio.Event,
        mock: MagicMock,
        queue,
    ):
        @broker.subscriber(stream=StreamSub(queue, polling_interval=3000))
        async def handler(msg):
            mock(msg)
            event.set()

        async with broker:
            await broker.start()

            await asyncio.wait(
                (
                    asyncio.create_task(
                        broker._connection.xadd(queue, {"message": "hello"})
                    ),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        mock.assert_called_once_with({"message": "hello"})

    async def test_consume_stream_batch(
        self,
        broker: RedisBroker,
        event: asyncio.Event,
        mock: MagicMock,
        queue,
    ):
        @broker.subscriber(stream=StreamSub(queue, polling_interval=3000, batch=True))
        async def handler(msg):
            mock(msg)
            event.set()

        async with broker:
            await broker.start()

            await asyncio.wait(
                (
                    asyncio.create_task(broker.publish("hello", stream=queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        mock.assert_called_once_with(["hello"])

    async def test_consume_stream_batch_native(
        self,
        broker: RedisBroker,
        event: asyncio.Event,
        mock: MagicMock,
        queue,
    ):
        @broker.subscriber(stream=StreamSub(queue, polling_interval=3000, batch=True))
        async def handler(msg):
            mock(msg)
            event.set()

        async with broker:
            await broker.start()

            await asyncio.wait(
                (
                    asyncio.create_task(
                        broker._connection.xadd(queue, {"message": "hello"})
                    ),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        mock.assert_called_once_with([{"message": "hello"}])

    @pytest.mark.asyncio()
    async def test_consume_nack(
        self,
        queue: str,
        full_broker: RedisBroker,
        event: asyncio.Event,
    ):
        @full_broker.subscriber(stream=StreamSub(queue, group="group", consumer=queue))
        async def handler(msg: RedisMessage):
            event.set()
            await msg.nack()

        async with full_broker:
            await full_broker.start()

            with patch.object(Redis, "xack", spy_decorator(Redis.xack)) as m:
                await asyncio.wait(
                    (
                        asyncio.create_task(full_broker.publish("hello", stream=queue)),
                        asyncio.create_task(event.wait()),
                    ),
                    timeout=3,
                )

                assert not m.mock.called

        assert event.is_set()

    @pytest.mark.asyncio()
    async def test_consume_ack(
        self,
        queue: str,
        full_broker: RedisBroker,
        event: asyncio.Event,
    ):
        @full_broker.subscriber(stream=StreamSub(queue, group="group", consumer=queue))
        async def handler(msg: RedisMessage):
            event.set()

        async with full_broker:
            await full_broker.start()

            with patch.object(Redis, "xack", spy_decorator(Redis.xack)) as m:
                await asyncio.wait(
                    (
                        asyncio.create_task(full_broker.publish("hello", stream=queue)),
                        asyncio.create_task(event.wait()),
                    ),
                    timeout=3,
                )

                m.mock.assert_called_once()

        assert event.is_set()
