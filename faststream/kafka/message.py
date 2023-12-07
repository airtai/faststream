from typing import Any, Generic, Optional, Sequence, Tuple, TypeVar

import aiokafka
from pydantic.dataclasses import dataclass

from faststream.broker.message import StreamMessage

KT = TypeVar("KT")
VT = TypeVar("VT")

_missing = object()


@dataclass
class ConsumerRecord(Generic[KT, VT]):
    topic: str
    "The topic this record is received from"

    partition: int
    "The partition from which this record is received"

    offset: int
    "The position of this record in the corresponding Kafka partition."

    timestamp: int
    "The timestamp of this record"

    timestamp_type: int
    "The timestamp type of this record"

    key: Optional[KT]
    "The key (or `None` if no key is specified)"

    value: Optional[VT]
    "The value"

    checksum: int
    "Deprecated"

    serialized_key_size: int
    "The size of the serialized, uncompressed key in bytes."

    serialized_value_size: int
    "The size of the serialized, uncompressed value in bytes."

    headers: Sequence[Tuple[str, bytes]]
    "The headers"


class KafkaMessage(StreamMessage[ConsumerRecord]):
    """
    Represents a Kafka message in the FastStream framework.

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
        consumer: aiokafka.AIOKafkaConsumer,
        is_manual: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)

        self.is_manual = is_manual
        self.consumer = consumer

    async def ack(self, **kwargs: Any) -> None:
        """
        Acknowledge the Kafka message.

        Args:
            **kwargs (Any): Additional keyword arguments.

        Returns:
            None: This method does not return a value.
        """
        if self.is_manual and not self.commited:
            await self.consumer.commit()
            await super().ack()
