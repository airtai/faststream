from typing import Any, Protocol, Union

from aiokafka import (
    AIOKafkaConsumer,
    ConsumerRecord,
    TopicPartition as AIOKafkaTopicPartition,
)

from faststream.message import AckStatus, StreamMessage


class ConsumerProtocol(Protocol):
    """A protocol for Kafka consumers."""

    async def commit(self) -> None: ...

    def seek(
        self,
        partition: AIOKafkaTopicPartition,
        offset: int,
    ) -> None:
        pass


class FakeConsumer:
    """A fake Kafka consumer."""

    async def commit(self) -> None:
        pass

    def seek(
        self,
        partition: AIOKafkaTopicPartition,
        offset: int,
    ) -> None:
        pass


FAKE_CONSUMER = FakeConsumer()


class KafkaRawMessage(ConsumerRecord[Any, Any]):  # type: ignore[misc]
    consumer: AIOKafkaConsumer


class KafkaMessage(
    StreamMessage[
        Union[
            "ConsumerRecord[Any, Any]",
            tuple["ConsumerRecord[Any, Any]", ...],
        ]
    ],
):
    """Represents a Kafka message in the FastStream framework.

    This class extends `StreamMessage` and is specialized for handling Kafka ConsumerRecord objects.
    """

    def __init__(self, *args: Any, consumer: ConsumerProtocol, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.consumer = consumer
        self.committed = AckStatus.ACKED


class KafkaAckableMessage(KafkaMessage):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.committed = None

    async def ack(self) -> None:
        if not self.committed:
            await self.consumer.commit()
        await super().ack()

    async def reject(self) -> None:
        await self.ack()

    async def nack(self) -> None:
        if not self.committed:
            raw_messages = (
                self.raw_message
                if isinstance(self.raw_message, tuple)
                else (self.raw_message,)
            )
            # A batch can span partitions: rewind each one to the first offset
            # the batch holds there, or the others' offsets get committed later.
            first_offsets: dict[AIOKafkaTopicPartition, int] = {}
            for raw_message in raw_messages:
                topic_partition = AIOKafkaTopicPartition(
                    raw_message.topic,
                    raw_message.partition,
                )
                offset = first_offsets.get(topic_partition)
                if offset is None or raw_message.offset < offset:
                    first_offsets[topic_partition] = raw_message.offset
            for topic_partition, offset in first_offsets.items():
                self.consumer.seek(
                    partition=topic_partition,
                    offset=offset,
                )
        await super().nack()
