from typing import Dict, Optional
from uuid import uuid4

from aiokafka import AIOKafkaProducer

from faststream.broker.parsers import encode_message
from faststream.exceptions import NOT_CONNECTED_YET
from faststream.types import SendableMessage


class AioKafkaFastProducer:
    """A class to represent a fast Kafka producer.

    Attributes:
        _producer : AIOKafkaProducer object representing the Kafka producer

    Methods:
        publish : Publishes a message to a Kafka topic.
        stop : Stops the Kafka producer.
        publish_batch : Publishes a batch of messages to a Kafka topic.
    """

    _producer: Optional[AIOKafkaProducer]

    def __init__(
        self,
        producer: AIOKafkaProducer,
    ) -> None:
        """Initialize the class.

        Args:
            producer: An instance of AIOKafkaProducer.
        """
        self._producer = producer

    async def publish(
        self,
        message: SendableMessage,
        topic: str,
        key: Optional[bytes] = None,
        partition: Optional[int] = None,
        timestamp_ms: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None,
        *,
        reply_to: str = "",
    ) -> None:
        """Publish a message to a topic.

        Args:
            message: The message to be published.
            topic: The topic to publish the message to.
            key: The key associated with the message.
            partition: The partition to which the message should be sent.
            timestamp_ms: The timestamp of the message in milliseconds.
            headers: Additional headers to be included with the message.
            correlation_id: The correlation ID of the message.
            reply_to: The topic to which the reply should be sent.

        Returns:
            None

        Raises:
            AssertionError: If the broker is not connected.
        """
        assert self._producer, NOT_CONNECTED_YET  # nosec B101

        message, content_type = encode_message(message)

        headers_to_send = {
            "content-type": content_type or "",
            "correlation_id": correlation_id or str(uuid4()),
            **(headers or {}),
        }

        if reply_to:
            headers_to_send["reply_to"] = headers_to_send.get(
                "reply_to",
                reply_to,
            )

        await self._producer.send(
            topic=topic,
            value=message,
            key=key,
            partition=partition,
            timestamp_ms=timestamp_ms,
            headers=[(i, (j or "").encode())
                     for i, j in headers_to_send.items()],
        )

    async def stop(self) -> None:
        if self._producer is not None:  # pragma: no branch
            await self._producer.stop()

    async def publish_batch(
        self,
        *msgs: SendableMessage,
        topic: str,
        partition: Optional[int] = None,
        timestamp_ms: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        reply_to: str = "",
        correlation_id: Optional[str] = None,
    ) -> None:
        """Publish a batch of messages to a topic."""
        assert self._producer, NOT_CONNECTED_YET  # nosec B101

        batch = self._producer.create_batch()

        headers_to_send = {
            "correlation_id": correlation_id or str(uuid4()),
            **(headers or {})
        }

        if reply_to:
            headers_to_send["reply_to"] = headers_to_send.get(
                "reply_to",
                reply_to,
            )

        for msg in msgs:
            message, content_type = encode_message(msg)

            if content_type:
                final_headers = {
                    "content-type": content_type,
                    **headers_to_send,
                }
            else:
                final_headers = headers_to_send.copy()

            batch.append(
                key=None,
                value=message,
                timestamp=timestamp_ms,
                headers=[(i, j.encode()) for i, j in final_headers.items()],
            )

        await self._producer.send_batch(batch, topic, partition=partition)
