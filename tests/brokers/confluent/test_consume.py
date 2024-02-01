import asyncio
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from faststream import Context, Depends
from faststream.broker.core.abc import BrokerUsecase
from faststream.confluent import KafkaBroker
from faststream.confluent.annotations import KafkaMessage
from faststream.confluent.client import AsyncConfluentConsumer
from faststream.exceptions import AckMessage, StopConsume

# from tests.brokers.base.consume import BrokerRealConsumeTestcase
from tests.tools import spy_decorator


@pytest.mark.asyncio()
@pytest.mark.confluent()
class BrokerConsumeTestcase:  # noqa: D101
    @pytest.fixture()
    def consume_broker(self, broker: BrokerUsecase):
        return broker

    async def test_consume(
        self,
        queue: str,
        consume_broker: BrokerUsecase,
        event: asyncio.Event,
    ):
        @consume_broker.subscriber(queue, auto_offset_reset="earliest")
        def subscriber(m):
            event.set()

        async with consume_broker:
            await consume_broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(consume_broker.publish("hello", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=10,
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

        @consume_broker.subscriber(queue, auto_offset_reset="earliest")
        @consume_broker.subscriber(queue + "1", auto_offset_reset="earliest")
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
                timeout=10,
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

        @consume_broker.subscriber(queue, auto_offset_reset="earliest")
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
                timeout=10,
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

        @consume_broker.subscriber(queue, auto_offset_reset="earliest")
        def handler(m):
            mock.handler()
            consume.set()

        another_topic = queue + "1"

        @consume_broker.subscriber(another_topic, auto_offset_reset="earliest")
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
                timeout=10,
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
            auto_offset_reset="earliest",
        )
        async def handler(m):
            mock.handler(m)
            consume.set()

        @consume_broker.subscriber(queue, auto_offset_reset="earliest")
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
                timeout=10,
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

        @consume_broker.subscriber(queue, auto_offset_reset="earliest")
        async def handler(m: Foo, dep: int = Depends(dependency), broker=Context()):
            mock(m, dep, broker)
            event.set()

        await consume_broker.start()
        await asyncio.wait(
            (
                asyncio.create_task(consume_broker.publish({"x": 1}, queue)),
                asyncio.create_task(event.wait()),
            ),
            timeout=10,
        )

        assert event.is_set()
        mock.assert_called_once_with({"x": 1}, "100", consume_broker)


@pytest.mark.asyncio()
@pytest.mark.confluent()
class BrokerRealConsumeTestcase(BrokerConsumeTestcase):  # noqa: D101
    @pytest.mark.slow()
    async def test_stop_consume_exc(
        self,
        queue: str,
        consume_broker: BrokerUsecase,
        event: asyncio.Event,
        mock: MagicMock,
    ):
        @consume_broker.subscriber(queue, auto_offset_reset="earliest")
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
                timeout=10,
            )
            await asyncio.sleep(0.5)
            await consume_broker.publish("hello", queue)
            await asyncio.sleep(0.5)

        assert event.is_set()
        mock.assert_called_once()


@pytest.mark.confluent()
class TestConsume(BrokerRealConsumeTestcase):
    """A class to represent a test Kafka broker."""

    @pytest.mark.asyncio()
    async def test_consume_single_message(
        self,
        confluent_kafka_topic: str,
        consume_broker: KafkaBroker,
        event: asyncio.Event,
    ):
        @consume_broker.subscriber(confluent_kafka_topic, auto_offset_reset="earliest")
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
                timeout=10,
            )

        assert event.is_set()

    @pytest.mark.asyncio()
    async def test_consume_batch(self, confluent_kafka_topic: str, broker: KafkaBroker):
        msgs_queue = asyncio.Queue(maxsize=1)

        @broker.subscriber(
            confluent_kafka_topic, batch=True, auto_offset_reset="earliest"
        )
        async def handler(msg):
            await msgs_queue.put(msg)

        async with broker:
            await broker.start()

            await broker.publish_batch(1, "hi", topic=confluent_kafka_topic)

            result, _ = await asyncio.wait(
                (asyncio.create_task(msgs_queue.get()),),
                timeout=10,
            )

        assert [{1, "hi"}] == [set(r.result()) for r in result]

    @pytest.mark.asyncio()
    @pytest.mark.slow()
    async def test_consume_ack(
        self,
        queue: str,
        full_broker: KafkaBroker,
        event: asyncio.Event,
    ):
        @full_broker.subscriber(
            queue, group_id="test", auto_commit=False, auto_offset_reset="earliest"
        )
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

    @pytest.mark.asyncio()
    @pytest.mark.slow()
    async def test_consume_ack_manual(
        self,
        queue: str,
        full_broker: KafkaBroker,
        event: asyncio.Event,
    ):
        @full_broker.subscriber(
            queue, group_id="test", auto_commit=False, auto_offset_reset="earliest"
        )
        async def handler(msg: KafkaMessage):
            await msg.ack()
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

    @pytest.mark.asyncio()
    @pytest.mark.slow()
    async def test_consume_ack_raise(
        self,
        queue: str,
        full_broker: KafkaBroker,
        event: asyncio.Event,
    ):
        @full_broker.subscriber(
            queue, group_id="test", auto_commit=False, auto_offset_reset="earliest"
        )
        async def handler(msg: KafkaMessage):
            event.set()
            raise AckMessage()

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

    @pytest.mark.asyncio()
    @pytest.mark.slow()
    async def test_nack(
        self,
        queue: str,
        full_broker: KafkaBroker,
        event: asyncio.Event,
    ):
        @full_broker.subscriber(
            queue, group_id="test", auto_commit=False, auto_offset_reset="earliest"
        )
        async def handler(msg: KafkaMessage):
            await msg.nack()
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
                assert not m.mock.called

        assert event.is_set()

    @pytest.mark.asyncio()
    @pytest.mark.slow()
    async def test_consume_no_ack(
        self,
        queue: str,
        full_broker: KafkaBroker,
        event: asyncio.Event,
    ):
        @full_broker.subscriber(
            queue, group_id="test", no_ack=True, auto_offset_reset="earliest"
        )
        async def handler(msg: KafkaMessage):
            event.set()

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
            m.mock.assert_not_called()

        assert event.is_set()
