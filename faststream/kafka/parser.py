from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from faststream.broker.message import decode_message, gen_cor_id
from faststream.kafka.message import FAKE_CONSUMER, KafkaMessage
from faststream.utils.context.repository import context

if TYPE_CHECKING:
    from aiokafka import ConsumerRecord

    from faststream.broker.message import StreamMessage
    from faststream.kafka.subscriber.usecase import LogicSubscriber
    from faststream.types import DecodedMessage


class AioKafkaParser:
    """A class to parse Kafka messages."""

    @staticmethod
    async def parse_message(
        message: "ConsumerRecord",
    ) -> "StreamMessage[ConsumerRecord]":
        """Parses a Kafka message."""
        headers = {i: j.decode() for i, j in message.headers}
        handler: Optional["LogicSubscriber[Any]"] = context.get_local("handler_")
        return KafkaMessage(
            body=message.value,
            headers=headers,
            reply_to=headers.get("reply_to", ""),
            content_type=headers.get("content-type"),
            message_id=f"{message.offset}-{message.timestamp}",
            correlation_id=headers.get("correlation_id", gen_cor_id()),
            raw_message=message,
            consumer=getattr(handler, "consumer", None) or FAKE_CONSUMER,
            is_manual=getattr(handler, "is_manual", True),
        )

    @staticmethod
    async def parse_message_batch(
        message: Tuple["ConsumerRecord", ...],
    ) -> "StreamMessage[Tuple[ConsumerRecord, ...]]":
        """Parses a batch of messages from a Kafka consumer."""
        body: List[Any] = []
        batch_headers: List[Dict[str, str]] = []

        first = message[0]
        last = message[-1]

        for m in message:
            body.append(m.value)
            batch_headers.append({i: j.decode() for i, j in m.headers})

        headers = next(iter(batch_headers), {})

        handler: Optional["LogicSubscriber[Any]"] = context.get_local("handler_")

        return KafkaMessage(
            body=body,
            headers=headers,
            batch_headers=batch_headers,
            reply_to=headers.get("reply_to", ""),
            content_type=headers.get("content-type"),
            message_id=f"{first.offset}-{last.offset}-{first.timestamp}",
            correlation_id=headers.get("correlation_id", gen_cor_id()),
            raw_message=message,
            consumer=getattr(handler, "consumer", None) or FAKE_CONSUMER,
            is_manual=getattr(handler, "is_manual", True),
        )

    @staticmethod
    async def decode_message(msg: "StreamMessage[ConsumerRecord]") -> "DecodedMessage":
        """Decodes a message."""
        return decode_message(msg)

    @classmethod
    async def decode_message_batch(
        cls,
        msg: "StreamMessage[Tuple[ConsumerRecord, ...]]",
    ) -> "DecodedMessage":
        """Decode a batch of messages."""
        return [decode_message(await cls.parse_message(m)) for m in msg.raw_message]
