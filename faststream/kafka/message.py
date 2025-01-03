from dataclasses import dataclass
from typing import Any, Protocol, Tuple, Union

from aiokafka import AIOKafkaConsumer, ConsumerRecord
from aiokafka import TopicPartition as AIOKafkaTopicPartition

from faststream.broker.message import StreamMessage


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


@dataclass
class KafkaRawMessage(ConsumerRecord):  # type: ignore[misc]
    consumer: AIOKafkaConsumer


class KafkaMessage(
    StreamMessage[
        Union[
            "ConsumerRecord",
            Tuple["ConsumerRecord", ...],
        ]
    ]
):
    """Represents a Kafka message in the FastStream framework.

    This class extends `StreamMessage` and is specialized for handling Kafka ConsumerRecord objects.
    """

    def __init__(
        self,
        *args: Any,
        consumer: ConsumerProtocol,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)

        self.consumer = consumer

    async def nack(self) -> None:
        """Reject the Kafka message."""
        if not self.committed:
            raw_message = (
                self.raw_message[0]
                if isinstance(self.raw_message, tuple)
                else self.raw_message
            )
            topic_partition = AIOKafkaTopicPartition(
                raw_message.topic,
                raw_message.partition,
            )
            self.consumer.seek(
                partition=topic_partition,
                offset=raw_message.offset,
            )
        await super().nack()


class KafkaAckableMessage(KafkaMessage):
    async def ack(self) -> None:
        """Acknowledge the Kafka message."""
        if not self.committed:
            await self.consumer.commit()
        await super().ack()
