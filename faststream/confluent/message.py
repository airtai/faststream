from typing import Any, Protocol, Tuple, Union

from confluent_kafka import Message

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


class KafkaMessage(StreamMessage[Union[
    Message,
    Tuple[Message, ...],
]]):
    """Represents a Kafka message in the FastStream framework.

    This class extends `StreamMessage` and is specialized for handling confluent_kafka.Message objects.
    """

    def __init__(
        self,
        *args: Any,
        consumer: ConsumerProtocol,
        is_manual: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)

        self.is_manual = is_manual
        self.consumer = consumer

    async def ack(self) -> None:
        """Acknowledge the Kafka message."""
        if self.is_manual and not self.committed:
            await self.consumer.commit()
            await super().ack()
