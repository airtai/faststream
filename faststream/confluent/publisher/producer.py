from typing import TYPE_CHECKING, Dict, Optional

from typing_extensions import override

from faststream.broker.message import encode_message
from faststream.broker.publisher.proto import ProducerProto
from faststream.exceptions import NOT_CONNECTED_YET

if TYPE_CHECKING:
    from faststream.confluent.client import AsyncConfluentProducer
    from faststream.types import SendableMessage


class AsyncConfluentFastProducer(ProducerProto):
    """A class to represent Kafka producer."""

    _producer: Optional["AsyncConfluentProducer"]

    def __init__(
        self,
        producer: "AsyncConfluentProducer",
    ) -> None:
        self._producer = producer

    @override
    async def publish(  # type: ignore[override]
        self,
        message: "SendableMessage",
        topic: str,
        *,
        key: Optional[bytes] = None,
        partition: Optional[int] = None,
        timestamp_ms: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        correlation_id: str = "",
        reply_to: str = "",
    ) -> None:
        """Publish a message to a topic."""
        assert self._producer, NOT_CONNECTED_YET  # nosec B101

        message, content_type = encode_message(message)

        headers_to_send = {
            "content-type": content_type or "",
            "correlation_id": correlation_id,
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
            headers=[(i, (j or "").encode()) for i, j in headers_to_send.items()],
        )

    async def stop(self) -> None:
        if self._producer is not None:  # pragma: no branch
            await self._producer.stop()

    async def publish_batch(
        self,
        *msgs: "SendableMessage",
        topic: str,
        partition: Optional[int] = None,
        timestamp_ms: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        reply_to: str = "",
        correlation_id: str = "",
    ) -> None:
        """Publish a batch of messages to a topic."""
        assert self._producer, NOT_CONNECTED_YET  # nosec B101

        batch = self._producer.create_batch()

        headers_to_send = {"correlation_id": correlation_id, **(headers or {})}

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
