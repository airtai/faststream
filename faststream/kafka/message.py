from typing import TYPE_CHECKING, Any, Protocol, Tuple, Union

from faststream.broker.message import StreamMessage

if TYPE_CHECKING:
    from aiokafka import ConsumerRecord


class ConsumerProtocol(Protocol):
    """A protocol for Kafka consumers."""

    async def commit(self) -> None: ...


class FakeConsumer:
    """A fake Kafka consumer."""

    async def commit(self) -> None:
        pass


FAKE_CONSUMER = FakeConsumer()


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
