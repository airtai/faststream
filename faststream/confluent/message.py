from typing import Any

import confluent_kafka

from faststream.broker.message import StreamMessage
from faststream.confluent.client import AsyncConfluentConsumer


class KafkaMessage(StreamMessage[confluent_kafka.Message]):
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
        consumer: AsyncConfluentConsumer,
        is_manual: bool = False,
        **kwargs: Any,
    ) -> None:
        """Constructor method for the KafkaMessage class.

        Args:
            *args (Any): Additional positional arguments.
            consumer (AsyncConfluentConsumer): The Kafka consumer that received the message.
            is_manual (bool): Whether the consumer is manual or not.
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
        if self.is_manual and not self.commited:
            await self.consumer.commit()
            await super().ack()