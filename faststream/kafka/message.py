from typing import Any, Protocol

import aiokafka

from faststream.broker.message import StreamMessage


class ConsumerProtocol(Protocol):
    """A protocol for Kafka consumers."""

    async def commit(self) -> None:
        ...


class FakeConsumer:
    """A fake Kafka consumer."""

    async def commit(self) -> None:
        pass


FAKE_CONSUMER = FakeConsumer()


class KafkaMessage(StreamMessage[aiokafka.ConsumerRecord]):
    """Represents a Kafka message in the FastStream framework.

    This class extends `StreamMessage` and is specialized for handling Kafka ConsumerRecord objects.

    Methods:
        ack(**kwargs) -> None:
            Acknowledge the Kafka message.

        nack(**kwargs) -> None:
            Negative acknowledgment of the Kafka message.

        reject(**kwargs) -> None:
            Reject the Kafka message.
    """

    def __init__(
        self,
        *args: Any,
        consumer: ConsumerProtocol,
        is_manual: bool = False,
        **kwargs: Any,
    ) -> None:
        """Initialize the KafkaMessage object.

        Args:
            *args (Any): Additional positional arguments.
            consumer (aiokafka.AIOKafkaConsumer): The Kafka consumer.
            is_manual (bool): Whether the message is manually acknowledged.
            **kwargs (Any): Additional keyword arguments.
        """
        super().__init__(*args, **kwargs)

        self.is_manual = is_manual
        self.consumer = consumer

    async def ack(self, **kwargs: Any) -> None:
        """Acknowledge the Kafka message.

        Args:
            **kwargs (Any): Additional keyword arguments.

        Returns:
            None: This method does not return a value.
        """
        if self.is_manual and not self.committed:
            await self.consumer.commit()
            await super().ack()
