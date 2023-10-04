import asyncio
from unittest.mock import patch

import pytest
from aiokafka import AIOKafkaConsumer

from faststream.exceptions import AckMessage
from faststream.kafka import KafkaBroker
from faststream.kafka.annotations import KafkaMessage
from tests.brokers.base.consume import BrokerRealConsumeTestcase
from tests.tools import spy_decorator


@pytest.mark.kafka
class TestConsume(BrokerRealConsumeTestcase):
    @pytest.mark.asyncio
    async def test_consume_batch(self, queue: str, broker: KafkaBroker):
        msgs_queue = asyncio.Queue(maxsize=1)

        @broker.subscriber(queue, batch=True)
        async def handler(msg):
            await msgs_queue.put(msg)

        async with broker:
            await broker.start()

            await broker.publish_batch(1, "hi", topic=queue)

            result, _ = await asyncio.wait(
                (asyncio.create_task(msgs_queue.get()),),
                timeout=3,
            )

        assert [{1, "hi"}] == [set(r.result()) for r in result]

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_consume_ack(
        self,
        queue: str,
        full_broker: KafkaBroker,
        event: asyncio.Event,
    ):
        @full_broker.subscriber(queue, group_id="test", auto_commit=False)
        async def handler(msg: KafkaMessage):
            event.set()

        await full_broker.start()
        with patch.object(
            AIOKafkaConsumer, "commit", spy_decorator(AIOKafkaConsumer.commit)
        ) as m:
            await asyncio.wait(
                (
                    asyncio.create_task(
                        full_broker.publish(
                            "hello",
                            queue,
                        )
                    ),
                    asyncio.create_task(event.wait()),
                ),
                timeout=10,
            )
            m.mock.assert_called_once()

        assert event.is_set()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_consume_ack_manual(
        self,
        queue: str,
        full_broker: KafkaBroker,
        event: asyncio.Event,
    ):
        @full_broker.subscriber(queue, group_id="test", auto_commit=False)
        async def handler(msg: KafkaMessage):
            await msg.ack()
            event.set()

        await full_broker.start()
        with patch.object(
            AIOKafkaConsumer, "commit", spy_decorator(AIOKafkaConsumer.commit)
        ) as m:
            await asyncio.wait(
                (
                    asyncio.create_task(
                        full_broker.publish(
                            "hello",
                            queue,
                        )
                    ),
                    asyncio.create_task(event.wait()),
                ),
                timeout=10,
            )
            m.mock.assert_called_once()

        assert event.is_set()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_consume_ack_raise(
        self,
        queue: str,
        full_broker: KafkaBroker,
        event: asyncio.Event,
    ):
        @full_broker.subscriber(queue, group_id="test", auto_commit=False)
        async def handler(msg: KafkaMessage):
            event.set()
            raise AckMessage()

        await full_broker.start()
        with patch.object(
            AIOKafkaConsumer, "commit", spy_decorator(AIOKafkaConsumer.commit)
        ) as m:
            await asyncio.wait(
                (
                    asyncio.create_task(
                        full_broker.publish(
                            "hello",
                            queue,
                        )
                    ),
                    asyncio.create_task(event.wait()),
                ),
                timeout=10,
            )
            m.mock.assert_called_once()

        assert event.is_set()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_nack(
        self,
        queue: str,
        full_broker: KafkaBroker,
        event: asyncio.Event,
    ):
        @full_broker.subscriber(queue, group_id="test", auto_commit=False)
        async def handler(msg: KafkaMessage):
            await msg.nack()
            event.set()

        await full_broker.start()
        with patch.object(
            AIOKafkaConsumer, "commit", spy_decorator(AIOKafkaConsumer.commit)
        ) as m:
            await asyncio.wait(
                (
                    asyncio.create_task(
                        full_broker.publish(
                            "hello",
                            queue,
                        )
                    ),
                    asyncio.create_task(event.wait()),
                ),
                timeout=10,
            )
            assert not m.mock.called

        assert event.is_set()
