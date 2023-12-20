import asyncio
from unittest.mock import patch

import pytest
from aiokafka import AIOKafkaConsumer

from faststream.exceptions import AckMessage
from faststream.kafka import ConfluentKafkaBroker
from faststream.kafka.annotations import KafkaMessage
from faststream.kafka.client import AsyncConfluentConsumer
from tests.brokers.base.consume import BrokerRealConsumeTestcase
from tests.tools import spy_decorator


@pytest.mark.confluent
class TestConsume(BrokerRealConsumeTestcase):
    @pytest.mark.asyncio
    async def test_consume_single_message(
        self,
        confluent_kafka_topic: str,
        consume_broker: ConfluentKafkaBroker,
        event: asyncio.Event,
    ):
        @consume_broker.subscriber(confluent_kafka_topic)
        def subscriber(m):
            event.set()

        async with consume_broker:
            await consume_broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(
                        consume_broker.publish("hello", confluent_kafka_topic)
                    ),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        assert event.is_set()

    @pytest.mark.asyncio
    async def test_consume_batch(
        self, confluent_kafka_topic: str, broker: ConfluentKafkaBroker
    ):
        msgs_queue = asyncio.Queue(maxsize=1)

        @broker.subscriber(confluent_kafka_topic, batch=True)
        async def handler(msg):
            print(f"At handler - {msg}")
            await msgs_queue.put(msg)

        async with broker:
            await broker.start()
            # await asyncio.sleep(3)
            await broker.publish_batch(1, "hi", topic=confluent_kafka_topic)

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
        full_broker: ConfluentKafkaBroker,
        event: asyncio.Event,
    ):
        @full_broker.subscriber(queue, group_id="test", auto_commit=False)
        async def handler(msg: KafkaMessage):
            event.set()

        async with full_broker:
            await full_broker.start()

            with patch.object(
                AsyncConfluentConsumer,
                "commit",
                spy_decorator(AsyncConfluentConsumer.commit),
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
        full_broker: ConfluentKafkaBroker,
        event: asyncio.Event,
    ):
        @full_broker.subscriber(queue, group_id="test", auto_commit=False)
        async def handler(msg: KafkaMessage):
            await msg.ack()
            event.set()

        async with full_broker:
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
        full_broker: ConfluentKafkaBroker,
        event: asyncio.Event,
    ):
        @full_broker.subscriber(queue, group_id="test", auto_commit=False)
        async def handler(msg: KafkaMessage):
            event.set()
            raise AckMessage()

        async with full_broker:
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
        full_broker: ConfluentKafkaBroker,
        event: asyncio.Event,
    ):
        @full_broker.subscriber(queue, group_id="test", auto_commit=False)
        async def handler(msg: KafkaMessage):
            await msg.nack()
            event.set()

        async with full_broker:
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

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_consume_no_ack(
        self,
        queue: str,
        full_broker: ConfluentKafkaBroker,
        event: asyncio.Event,
    ):
        @full_broker.subscriber(queue, group_id="test", no_ack=True)
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
            m.mock.assert_not_called()

        assert event.is_set()
