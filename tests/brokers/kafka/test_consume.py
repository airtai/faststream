import asyncio
from unittest.mock import MagicMock, patch

import pytest
from aiokafka import AIOKafkaConsumer
from aiokafka.structs import RecordMetadata

from faststream import AckPolicy
from faststream.exceptions import AckMessage
from faststream.kafka import TopicPartition
from faststream.kafka.annotations import KafkaMessage
from tests.brokers.base.consume import BrokerRealConsumeTestcase
from tests.tools import spy_decorator

from .basic import KafkaTestcaseConfig


@pytest.mark.kafka()
class TestConsume(KafkaTestcaseConfig, BrokerRealConsumeTestcase):
    @pytest.mark.asyncio()
    async def test_consume_by_pattern(
        self,
        queue: str,
    ) -> None:
        event = asyncio.Event()

        consume_broker = self.get_broker()

        @consume_broker.subscriber(queue)
        async def handler(msg) -> None:
            event.set()

        pattern_event = asyncio.Event()

        @consume_broker.subscriber(pattern=f"{queue[:-1]}*")
        async def pattern_handler(msg) -> None:
            pattern_event.set()

        async with self.patch_broker(consume_broker) as br:
            await br.start()
            result = await br.publish(1, topic=queue)
            assert isinstance(result, RecordMetadata), result

        await pattern_event.wait()
        assert pattern_event.is_set()

    @pytest.mark.asyncio()
    async def test_consume_batch(self, queue: str) -> None:
        consume_broker = self.get_broker()

        msgs_queue = asyncio.Queue(maxsize=1)

        @consume_broker.subscriber(queue, batch=True)
        async def handler(msg) -> None:
            await msgs_queue.put(msg)

        async with self.patch_broker(consume_broker) as br:
            await br.start()

            await br.publish_batch(1, "hi", topic=queue)

            result, _ = await asyncio.wait(
                (asyncio.create_task(msgs_queue.get()),),
                timeout=3,
            )

        assert [{1, "hi"}] == [set(r.result()) for r in result]

    @pytest.mark.asyncio()
    async def test_consume_batch_headers(
        self,
        mock,
        queue: str,
    ) -> None:
        event = asyncio.Event()

        consume_broker = self.get_broker(apply_types=True)

        @consume_broker.subscriber(queue, batch=True)
        def subscriber(m, msg: KafkaMessage) -> None:
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
    @pytest.mark.slow()
    async def test_consume_auto_ack(
        self,
        queue: str,
    ) -> None:
        event = asyncio.Event()

        consume_broker = self.get_broker(apply_types=True)

        @consume_broker.subscriber(
            queue, group_id="test", ack_policy=AckPolicy.REJECT_ON_ERROR
        )
        async def handler(msg: KafkaMessage) -> None:
            event.set()

        async with self.patch_broker(consume_broker) as br:
            await br.start()

            with patch.object(
                AIOKafkaConsumer,
                "commit",
                spy_decorator(AIOKafkaConsumer.commit),
            ) as m:
                await asyncio.wait(
                    (
                        asyncio.create_task(
                            consume_broker.publish(
                                "hello",
                                queue,
                            ),
                        ),
                        asyncio.create_task(event.wait()),
                    ),
                    timeout=10,
                )
                m.mock.assert_called_once()

        assert event.is_set()

    @pytest.mark.asyncio()
    async def test_manual_partition_consume(
        self,
        queue: str,
    ) -> None:
        event = asyncio.Event()

        consume_broker = self.get_broker()

        tp1 = TopicPartition(queue, partition=0)

        @consume_broker.subscriber(partitions=[tp1])
        async def handler_tp1(msg) -> None:
            event.set()

        async with self.patch_broker(consume_broker) as br:
            await br.start()

            await asyncio.wait(
                (
                    asyncio.create_task(br.publish("hello", queue, partition=0)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=10,
            )

        assert event.is_set()

    @pytest.mark.asyncio()
    @pytest.mark.slow()
    async def test_consume_ack_manual(
        self,
        queue: str,
    ) -> None:
        event = asyncio.Event()

        consume_broker = self.get_broker(apply_types=True)

        @consume_broker.subscriber(
            queue, group_id="test", ack_policy=AckPolicy.REJECT_ON_ERROR
        )
        async def handler(msg: KafkaMessage) -> None:
            await msg.ack()
            event.set()

        async with self.patch_broker(consume_broker) as br:
            await br.start()

            with patch.object(
                AIOKafkaConsumer,
                "commit",
                spy_decorator(AIOKafkaConsumer.commit),
            ) as m:
                await asyncio.wait(
                    (
                        asyncio.create_task(
                            br.publish(
                                "hello",
                                queue,
                            ),
                        ),
                        asyncio.create_task(event.wait()),
                    ),
                    timeout=10,
                )
                m.mock.assert_called_once()

        assert event.is_set()

    @pytest.mark.asyncio()
    @pytest.mark.slow()
    async def test_consume_ack_by_raise(
        self,
        queue: str,
    ) -> None:
        event = asyncio.Event()

        consume_broker = self.get_broker(apply_types=True)

        @consume_broker.subscriber(
            queue, group_id="test", ack_policy=AckPolicy.REJECT_ON_ERROR
        )
        async def handler(msg: KafkaMessage):
            event.set()
            raise AckMessage

        async with self.patch_broker(consume_broker) as br:
            await br.start()

            with patch.object(
                AIOKafkaConsumer,
                "commit",
                spy_decorator(AIOKafkaConsumer.commit),
            ) as m:
                await asyncio.wait(
                    (
                        asyncio.create_task(
                            br.publish(
                                "hello",
                                queue,
                            ),
                        ),
                        asyncio.create_task(event.wait()),
                    ),
                    timeout=10,
                )
                m.mock.assert_called_once()

        assert event.is_set()

    @pytest.mark.asyncio()
    @pytest.mark.slow()
    async def test_manual_nack(
        self,
        queue: str,
    ) -> None:
        event = asyncio.Event()

        consume_broker = self.get_broker(apply_types=True)

        @consume_broker.subscriber(
            queue, group_id="test", ack_policy=AckPolicy.REJECT_ON_ERROR
        )
        async def handler(msg: KafkaMessage) -> None:
            await msg.nack()
            event.set()

        async with self.patch_broker(consume_broker) as br:
            await br.start()

            with patch.object(
                AIOKafkaConsumer,
                "commit",
                spy_decorator(AIOKafkaConsumer.commit),
            ) as m:
                await asyncio.wait(
                    (
                        asyncio.create_task(
                            br.publish(
                                "hello",
                                queue,
                            ),
                        ),
                        asyncio.create_task(event.wait()),
                    ),
                    timeout=10,
                )
                assert not m.mock.called

        assert event.is_set()

    @pytest.mark.asyncio()
    @pytest.mark.slow()
    async def test_consume_no_ack(
        self,
        queue: str,
    ) -> None:
        event = asyncio.Event()

        consume_broker = self.get_broker(apply_types=True)

        @consume_broker.subscriber(
            queue, group_id="test", ack_policy=AckPolicy.DO_NOTHING
        )
        async def handler(msg: KafkaMessage) -> None:
            event.set()

        async with self.patch_broker(consume_broker) as br:
            await br.start()

            with patch.object(
                AIOKafkaConsumer,
                "commit",
                spy_decorator(AIOKafkaConsumer.commit),
            ) as m:
                await asyncio.wait(
                    (
                        asyncio.create_task(
                            br.publish(
                                "hello",
                                queue,
                            ),
                        ),
                        asyncio.create_task(event.wait()),
                    ),
                    timeout=10,
                )
                m.mock.assert_not_called()

            assert event.is_set()

    @pytest.mark.asyncio()
    @pytest.mark.slow()
    async def test_concurrent_consume(self, queue: str, mock: MagicMock) -> None:
        event = asyncio.Event()
        event2 = asyncio.Event()

        consume_broker = self.get_broker()

        args, kwargs = self.get_subscriber_params(queue, max_workers=2)

        @consume_broker.subscriber(*args, **kwargs)
        async def handler(msg) -> None:
            mock()
            if event.is_set():
                event2.set()
            else:
                event.set()

            # probably, we should increase it
            await asyncio.sleep(0.1)

        async with self.patch_broker(consume_broker) as br:
            await br.start()

            for i in range(5):
                await br.publish(i, queue)

        await asyncio.wait(
            (
                asyncio.create_task(event.wait()),
                asyncio.create_task(event2.wait()),
            ),
            timeout=3,
        )

        assert event.is_set()
        assert event2.is_set()
        assert mock.call_count == 2, mock.call_count

    @pytest.mark.asyncio()
    async def test_consume_without_value(
        self,
        mock: MagicMock,
        queue: str,
        event: asyncio.Event,
    ) -> None:
        consume_broker = self.get_broker()

        @consume_broker.subscriber(queue)
        async def handler(msg):
            event.set()
            mock(msg)

        async with self.patch_broker(consume_broker) as br:
            await br.start()

            await asyncio.wait(
                (
                    asyncio.create_task(
                        br._producer._producer.producer.send(queue, key=b"")
                    ),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

            mock.assert_called_once_with(b"")

    @pytest.mark.asyncio()
    async def test_consume_batch_without_value(
        self,
        mock: MagicMock,
        queue: str,
        event: asyncio.Event,
    ) -> None:
        consume_broker = self.get_broker()

        @consume_broker.subscriber(queue, batch=True)
        async def handler(msg):
            event.set()
            mock(msg)

        async with self.patch_broker(consume_broker) as br:
            await br.start()

            await asyncio.wait(
                (
                    asyncio.create_task(
                        br._producer._producer.producer.send(queue, key=b"")
                    ),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

            mock.assert_called_once_with([b""])
