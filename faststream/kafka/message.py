from typing import Any

import aiokafka

from faststream.broker.message import StreamMessage


class KafkaMessage(StreamMessage[aiokafka.ConsumerRecord]):
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

    async def ack(self, **kwargs: Any) -> None:
        """
        Acknowledge the Kafka message.

        Args:
            **kwargs (Any): Additional keyword arguments.

        Returns:
            None: This method does not return a value.
        """
        return None

    async def nack(self, **kwargs: Any) -> None:
        """
        Negative acknowledgment of the Kafka message.

        Args:
            **kwargs (Any): Additional keyword arguments.

        Returns:
            None: This method does not return a value.
        """
        return None

    async def reject(self, **kwargs: Any) -> None:
        """
        Reject the Kafka message.

        Args:
            **kwargs (Any): Additional keyword arguments.

        Returns:
            None: This method does not return a value.
        """
        return None
