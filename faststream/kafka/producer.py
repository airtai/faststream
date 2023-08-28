from typing import Dict, Optional
from uuid import uuid4

from aiokafka import AIOKafkaProducer, ConsumerRecord

from faststream.broker.parsers import encode_message, resolve_custom_func
from faststream.broker.types import (
    AsyncCustomDecoder,
    AsyncCustomParser,
    AsyncDecoder,
    AsyncParser,
)
from faststream.kafka.parser import AioKafkaParser
from faststream.types import SendableMessage


class AioKafkaFastProducer:
    _producer: Optional[AIOKafkaProducer]
    _decoder: AsyncDecoder[ConsumerRecord]
    _parser: AsyncParser[ConsumerRecord]

    def __init__(
        self,
        producer: AIOKafkaProducer,
        parser: Optional[AsyncCustomParser[ConsumerRecord]],
        decoder: Optional[AsyncCustomDecoder[ConsumerRecord]],
    ):
        self._producer = producer
        self._parser = resolve_custom_func(parser, AioKafkaParser.parse_message)
        self._decoder = resolve_custom_func(decoder, AioKafkaParser.decode_message)

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
    ) -> Optional[SendableMessage]:
        assert self._producer, "You need to connect broker at first"

        message, content_type = encode_message(message)

        headers_to_send = {
            "content-type": content_type or "",
            **(headers or {}),
        }

        if reply_to:
            headers_to_send.update(
                {
                    "reply_to": reply_to,
                    "correlation_id": correlation_id or str(uuid4()),
                }
            )

        await self._producer.send(
            topic=topic,
            value=message,
            key=key,
            partition=partition,
            timestamp_ms=timestamp_ms,
            headers=[(i, (j or "").encode()) for i, j in headers_to_send.items()],
        )

        return None

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
    ) -> None:
        assert self._producer, "You need to connect broker at first"

        batch = self._producer.create_batch()

        for msg in msgs:
            message, content_type = encode_message(msg)

            headers_to_send = {
                "content-type": content_type or "",
                **(headers or {}),
            }

            batch.append(
                key=None,
                value=message,
                timestamp=timestamp_ms,
                headers=[(i, j.encode()) for i, j in headers_to_send.items()],
            )

        await self._producer.send_batch(batch, topic, partition=partition)
