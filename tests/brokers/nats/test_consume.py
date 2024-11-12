import asyncio
from typing import Any
from unittest.mock import Mock, patch

import pytest
from nats.aio.msg import Msg
from nats.js.api import PubAck

from faststream import AckPolicy
from faststream.exceptions import AckMessage
from faststream.nats import ConsumerConfig, JStream, NatsBroker, PullSub
from faststream.nats.annotations import NatsMessage
from tests.brokers.base.consume import BrokerRealConsumeTestcase
from tests.tools import spy_decorator


@pytest.mark.nats()
class TestConsume(BrokerRealConsumeTestcase):
    def get_broker(self, apply_types: bool = False, **kwargs: Any) -> NatsBroker:
        return NatsBroker(apply_types=apply_types, **kwargs)

    async def test_consume_js(
        self,
        queue: str,
        stream: JStream,
    ) -> None:
        event = asyncio.Event()

        consume_broker = self.get_broker()

        @consume_broker.subscriber(queue, stream=stream)
        def subscriber(m) -> None:
            event.set()

        async with self.patch_broker(consume_broker) as br:
            await br.start()
            completed, _ = await asyncio.wait(
                (
                    asyncio.create_task(br.publish("hello", queue, stream=stream.name)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

            publish_with_stream_returns_ack_frame = False
            for task in completed:
                if isinstance(task.result(), PubAck):
                    publish_with_stream_returns_ack_frame = True
                    break

        assert event.is_set()
        assert publish_with_stream_returns_ack_frame

    async def test_consume_with_filter(
        self,
        queue,
        mock: Mock,
    ) -> None:
        event = asyncio.Event()

        consume_broker = self.get_broker()

        @consume_broker.subscriber(
            config=ConsumerConfig(filter_subjects=[f"{queue}.a"]),
            stream=JStream(queue, subjects=[f"{queue}.*"]),
        )
        def subscriber(m) -> None:
            mock(m)
            event.set()

        async with self.patch_broker(consume_broker) as br:
            await br.start()
            await asyncio.wait(
                (
                    asyncio.create_task(br.publish(2, f"{queue}.a")),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        assert event.is_set()
        mock.assert_called_once_with(2)

    async def test_consume_pull(
        self,
        queue: str,
        stream: JStream,
        mock,
    ) -> None:
        event = asyncio.Event()

        consume_broker = self.get_broker()

        @consume_broker.subscriber(
            queue,
            stream=stream,
            pull_sub=PullSub(1),
        )
        def subscriber(m) -> None:
            mock(m)
            event.set()

        async with self.patch_broker(consume_broker) as br:
            await br.start()

            await asyncio.wait(
                (
                    asyncio.create_task(br.publish("hello", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

            assert event.is_set()
            mock.assert_called_once_with("hello")

    async def test_consume_batch(
        self,
        queue: str,
        stream: JStream,
        mock,
    ) -> None:
        event = asyncio.Event()

        consume_broker = self.get_broker()

        @consume_broker.subscriber(
            queue,
            stream=stream,
            pull_sub=PullSub(1, batch=True),
        )
        def subscriber(m) -> None:
            mock(m)
            event.set()

        async with self.patch_broker(consume_broker) as br:
            await br.start()

            await asyncio.wait(
                (
                    asyncio.create_task(br.publish(b"hello", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

            assert event.is_set()
            mock.assert_called_once_with([b"hello"])

    async def test_consume_ack(
        self,
        queue: str,
        stream: JStream,
    ) -> None:
        event = asyncio.Event()

        consume_broker = self.get_broker(apply_types=True)

        @consume_broker.subscriber(queue, stream=stream)
        async def handler(msg: NatsMessage) -> None:
            event.set()

        async with self.patch_broker(consume_broker) as br:
            await br.start()

            with patch.object(Msg, "ack", spy_decorator(Msg.ack)) as m:
                await asyncio.wait(
                    (
                        asyncio.create_task(br.publish("hello", queue)),
                        asyncio.create_task(event.wait()),
                    ),
                    timeout=3,
                )
                m.mock.assert_called_once()

        assert event.is_set()

    async def test_core_consume_no_ack(
        self,
        queue: str,
        stream: JStream,
    ) -> None:
        event = asyncio.Event()

        consume_broker = self.get_broker(apply_types=True)

        @consume_broker.subscriber(queue, ack_policy=AckPolicy.DO_NOTHING)
        async def handler(msg: NatsMessage) -> None:
            event.set()

        async with self.patch_broker(consume_broker) as br:
            await br.start()

            with patch.object(Msg, "ack", spy_decorator(Msg.ack)) as m:
                await asyncio.wait(
                    (
                        asyncio.create_task(br.publish("hello", queue)),
                        asyncio.create_task(event.wait()),
                    ),
                    timeout=3,
                )
                assert not m.mock.called

        assert event.is_set()

    async def test_consume_ack_manual(
        self,
        queue: str,
        stream: JStream,
    ) -> None:
        event = asyncio.Event()

        consume_broker = self.get_broker(apply_types=True)

        @consume_broker.subscriber(queue, stream=stream)
        async def handler(msg: NatsMessage) -> None:
            await msg.ack()
            event.set()

        async with self.patch_broker(consume_broker) as br:
            await br.start()

            with patch.object(Msg, "ack", spy_decorator(Msg.ack)) as m:
                await asyncio.wait(
                    (
                        asyncio.create_task(br.publish("hello", queue)),
                        asyncio.create_task(event.wait()),
                    ),
                    timeout=3,
                )
                m.mock.assert_called_once()

        assert event.is_set()

    async def test_consume_ack_raise(
        self,
        queue: str,
        stream: JStream,
    ) -> None:
        event = asyncio.Event()

        consume_broker = self.get_broker(apply_types=True)

        @consume_broker.subscriber(queue, stream=stream)
        async def handler(msg: NatsMessage):
            event.set()
            raise AckMessage

        async with self.patch_broker(consume_broker) as br:
            await br.start()

            with patch.object(Msg, "ack", spy_decorator(Msg.ack)) as m:
                await asyncio.wait(
                    (
                        asyncio.create_task(br.publish("hello", queue)),
                        asyncio.create_task(event.wait()),
                    ),
                    timeout=3,
                )
                m.mock.assert_called_once()

        assert event.is_set()

    async def test_nack(
        self,
        queue: str,
        stream: JStream,
    ) -> None:
        event = asyncio.Event()

        consume_broker = self.get_broker(apply_types=True)

        @consume_broker.subscriber(queue, stream=stream)
        async def handler(msg: NatsMessage) -> None:
            await msg.nack()
            event.set()

        async with self.patch_broker(consume_broker) as br:
            await br.start()

            with patch.object(Msg, "nak", spy_decorator(Msg.nak)) as m:
                await asyncio.wait(
                    (
                        asyncio.create_task(br.publish("hello", queue)),
                        asyncio.create_task(event.wait()),
                    ),
                    timeout=3,
                )
                m.mock.assert_called_once()

        assert event.is_set()

    async def test_consume_no_ack(
        self,
        queue: str,
    ) -> None:
        event = asyncio.Event()

        consume_broker = self.get_broker(apply_types=True)

        @consume_broker.subscriber(queue, ack_policy=AckPolicy.DO_NOTHING)
        async def handler(msg: NatsMessage) -> None:
            event.set()

        async with self.patch_broker(consume_broker) as br:
            await br.start()

            with patch.object(Msg, "ack", spy_decorator(Msg.ack)) as m:
                await asyncio.wait(
                    (
                        asyncio.create_task(br.publish("hello", queue)),
                        asyncio.create_task(event.wait()),
                    ),
                    timeout=3,
                )
                m.mock.assert_not_called()

            assert event.is_set()

    async def test_consume_batch_headers(
        self,
        queue: str,
        stream: JStream,
        mock,
    ) -> None:
        event = asyncio.Event()

        consume_broker = self.get_broker(apply_types=True)

        @consume_broker.subscriber(
            queue,
            stream=stream,
            pull_sub=PullSub(1, batch=True),
        )
        def subscriber(m, msg: NatsMessage) -> None:
            check = all(
                (
                    msg.headers,
                    [msg.headers] == msg.batch_headers,
                    msg.headers.get("custom") == "1",
                ),
            )
            mock(check)
            event.set()

        async with self.patch_broker(consume_broker) as br:
            await br.start()
            await asyncio.wait(
                (
                    asyncio.create_task(br.publish("", queue, headers={"custom": "1"})),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        assert event.is_set()
        mock.assert_called_once_with(True)

    @pytest.mark.asyncio()
    async def test_consume_kv(
        self,
        queue: str,
        mock,
    ) -> None:
        event = asyncio.Event()

        consume_broker = self.get_broker(apply_types=True)

        @consume_broker.subscriber(queue, kv_watch=queue + "1")
        async def handler(m) -> None:
            mock(m)
            event.set()

        async with self.patch_broker(consume_broker) as br:
            await br.start()
            bucket = await br.key_value(queue + "1")

            await asyncio.wait(
                (
                    asyncio.create_task(
                        bucket.put(
                            queue,
                            b"world",
                        ),
                    ),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        assert event.is_set()
        mock.assert_called_with(b"world")

    @pytest.mark.asyncio()
    async def test_consume_os(
        self,
        queue: str,
        mock,
    ) -> None:
        event = asyncio.Event()

        consume_broker = self.get_broker(apply_types=True)

        @consume_broker.subscriber(queue, obj_watch=True)
        async def handler(filename: str) -> None:
            event.set()
            mock(filename)

        async with self.patch_broker(consume_broker) as br:
            await br.start()
            bucket = await br.object_storage(queue)

            await asyncio.wait(
                (
                    asyncio.create_task(
                        bucket.put(
                            "hello",
                            b"world",
                        ),
                    ),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        assert event.is_set()
        mock.assert_called_once_with("hello")

    async def test_get_one_js(
        self,
        queue: str,
        stream: JStream,
    ) -> None:
        broker = self.get_broker(apply_types=True)
        subscriber = broker.subscriber(queue, stream=stream)

        async with self.patch_broker(broker) as br:
            await br.start()

            message = None

            async def consume() -> None:
                nonlocal message
                message = await subscriber.get_one(timeout=5)

            async def publish() -> None:
                await br.publish("test_message", queue, stream=stream.name)

            await asyncio.wait(
                (
                    asyncio.create_task(consume()),
                    asyncio.create_task(publish()),
                ),
                timeout=10,
            )

            assert message is not None
            assert await message.decode() == "test_message"

    async def test_get_one_timeout_js(
        self,
        queue: str,
        stream: JStream,
        mock,
    ) -> None:
        broker = self.get_broker(apply_types=True)
        subscriber = broker.subscriber(queue, stream=stream)

        async with self.patch_broker(broker) as br:
            await br.start()

            mock(await subscriber.get_one(timeout=1e-24))
            mock.assert_called_once_with(None)

    async def test_get_one_pull(
        self,
        queue: str,
        stream: JStream,
    ) -> None:
        broker = self.get_broker(apply_types=True)
        subscriber = broker.subscriber(
            queue,
            stream=stream,
            pull_sub=PullSub(1),
        )

        async with self.patch_broker(broker) as br:
            await br.start()

            message = None

            async def consume() -> None:
                nonlocal message
                message = await subscriber.get_one(timeout=5)

            async def publish() -> None:
                await br.publish("test_message", queue)

            await asyncio.wait(
                (
                    asyncio.create_task(consume()),
                    asyncio.create_task(publish()),
                ),
                timeout=10,
            )

            assert message is not None
            assert await message.decode() == "test_message"

    async def test_get_one_pull_timeout(
        self,
        queue: str,
        stream: JStream,
        mock: Mock,
    ) -> None:
        broker = self.get_broker(apply_types=True)
        subscriber = broker.subscriber(
            queue,
            stream=stream,
            pull_sub=PullSub(1),
        )

        async with self.patch_broker(broker) as br:
            await br.start()

            mock(await subscriber.get_one(timeout=1e-24))
            mock.assert_called_once_with(None)

    async def test_get_one_batch(
        self,
        queue: str,
        stream: JStream,
    ) -> None:
        broker = self.get_broker(apply_types=True)
        subscriber = broker.subscriber(
            queue,
            stream=stream,
            pull_sub=PullSub(1, batch=True),
        )

        async with self.patch_broker(broker) as br:
            await br.start()

            message = None

            async def consume() -> None:
                nonlocal message
                message = await subscriber.get_one(timeout=5)

            async def publish() -> None:
                await br.publish("test_message", queue)

            await asyncio.wait(
                (
                    asyncio.create_task(consume()),
                    asyncio.create_task(publish()),
                ),
                timeout=10,
            )

            assert message is not None
            assert await message.decode() == ["test_message"]

    async def test_get_one_batch_timeout(
        self,
        queue: str,
        stream: JStream,
        mock: Mock,
    ) -> None:
        broker = self.get_broker(apply_types=True)
        subscriber = broker.subscriber(
            queue,
            stream=stream,
            pull_sub=PullSub(1, batch=True),
        )

        async with self.patch_broker(broker) as br:
            await br.start()

            mock(await subscriber.get_one(timeout=1e-24))
            mock.assert_called_once_with(None)

    async def test_get_one_with_filter(
        self,
        queue: str,
        stream: JStream,
    ) -> None:
        broker = self.get_broker(apply_types=True)
        subscriber = broker.subscriber(
            config=ConsumerConfig(filter_subjects=[f"{queue}.a"]),
            stream=JStream(queue, subjects=[f"{queue}.*"]),
        )

        async with self.patch_broker(broker) as br:
            await br.start()

            message = None

            async def consume() -> None:
                nonlocal message
                message = await subscriber.get_one(timeout=5)

            async def publish() -> None:
                await br.publish("test_message", f"{queue}.a")

            await asyncio.wait(
                (
                    asyncio.create_task(publish()),
                    asyncio.create_task(consume()),
                ),
                timeout=10,
            )

            assert message is not None
            assert await message.decode() == "test_message"

    async def test_get_one_kv(
        self,
        queue: str,
        stream: JStream,
    ) -> None:
        broker = self.get_broker(apply_types=True)
        subscriber = broker.subscriber(queue, kv_watch=queue + "1")

        async with self.patch_broker(broker) as br:
            await br.start()
            bucket = await br.key_value(queue + "1")

            message = None

            async def consume() -> None:
                nonlocal message
                message = await subscriber.get_one(timeout=5)

            async def publish() -> None:
                await bucket.put(queue, b"test_message")

            await asyncio.wait(
                (
                    asyncio.create_task(consume()),
                    asyncio.create_task(publish()),
                ),
                timeout=10,
            )

            assert message is not None
            assert await message.decode() == b"test_message"

    async def test_get_one_kv_timeout(
        self,
        queue: str,
        stream: JStream,
        mock: Mock,
    ) -> None:
        broker = self.get_broker(apply_types=True)
        subscriber = broker.subscriber(queue, kv_watch=queue + "1")

        async with self.patch_broker(broker) as br:
            await br.start()

            mock(await subscriber.get_one(timeout=1e-24))
            mock.assert_called_once_with(None)

    async def test_get_one_os(
        self,
        queue: str,
        stream: JStream,
    ) -> None:
        broker = self.get_broker(apply_types=True)
        subscriber = broker.subscriber(queue, obj_watch=True)

        async with self.patch_broker(broker) as br:
            await br.start()
            bucket = await br.object_storage(queue)

            new_object_id = None

            async def consume() -> None:
                nonlocal new_object_id
                new_object_event = await subscriber.get_one(timeout=5)
                new_object_id = await new_object_event.decode()

            async def publish() -> None:
                await bucket.put(queue, b"test_message")

            await asyncio.wait(
                (
                    asyncio.create_task(consume()),
                    asyncio.create_task(publish()),
                ),
                timeout=10,
            )

            new_object = await bucket.get(new_object_id)
            assert new_object.data == b"test_message"

    async def test_get_one_os_timeout(
        self,
        queue: str,
        stream: JStream,
        mock: Mock,
    ) -> None:
        broker = self.get_broker(apply_types=True)
        subscriber = broker.subscriber(queue, obj_watch=True)

        async with self.patch_broker(broker) as br:
            await br.start()

            mock(await subscriber.get_one(timeout=1e-24))
            mock.assert_called_once_with(None)
