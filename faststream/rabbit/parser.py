from typing import TYPE_CHECKING, Optional

from aio_pika import Message
from aio_pika.abc import DeliveryMode

from faststream.message import (
    StreamMessage,
    decode_message,
    encode_message,
    gen_cor_id,
)
from faststream.rabbit.message import RabbitMessage

if TYPE_CHECKING:
    from re import Pattern

    from aio_pika import IncomingMessage
    from aio_pika.abc import DateType, HeadersType

    from faststream._internal.basic_types import DecodedMessage
    from faststream.rabbit.types import AioPikaSendableMessage


class AioPikaParser:
    """A class for parsing, encoding, and decoding messages using aio-pika."""

    def __init__(self, pattern: Optional["Pattern[str]"] = None) -> None:
        self.pattern = pattern

    async def parse_message(
        self,
        message: "IncomingMessage",
    ) -> StreamMessage["IncomingMessage"]:
        """Parses an incoming message and returns a RabbitMessage object."""
        if (path_re := self.pattern) and (
            match := path_re.match(message.routing_key or "")
        ):
            path = match.groupdict()
        else:
            path = {}

        return RabbitMessage(
            body=message.body,
            headers=message.headers,
            reply_to=message.reply_to or "",
            content_type=message.content_type,
            message_id=message.message_id or gen_cor_id(),
            correlation_id=message.correlation_id or gen_cor_id(),
            path=path,
            raw_message=message,
        )

    async def decode_message(
        self,
        msg: StreamMessage["IncomingMessage"],
    ) -> "DecodedMessage":
        """Decode a message."""
        return decode_message(msg)

    @staticmethod
    def encode_message(
        message: "AioPikaSendableMessage",
        *,
        persist: bool = False,
        reply_to: Optional[str] = None,
        headers: Optional["HeadersType"] = None,
        content_type: Optional[str] = None,
        content_encoding: Optional[str] = None,
        priority: Optional[int] = None,
        correlation_id: Optional[str] = None,
        expiration: "DateType" = None,
        message_id: Optional[str] = None,
        timestamp: "DateType" = None,
        message_type: Optional[str] = None,
        user_id: Optional[str] = None,
        app_id: Optional[str] = None,
    ) -> Message:
        """Encodes a message for sending using AioPika."""
        if isinstance(message, Message):
            return message

        message_body, generated_content_type = encode_message(message)

        delivery_mode = (
            DeliveryMode.PERSISTENT if persist else DeliveryMode.NOT_PERSISTENT
        )

        return Message(
            message_body,
            content_type=content_type or generated_content_type,
            delivery_mode=delivery_mode,
            reply_to=reply_to,
            correlation_id=correlation_id or gen_cor_id(),
            headers=headers,
            content_encoding=content_encoding,
            priority=priority,
            expiration=expiration,
            message_id=message_id,
            timestamp=timestamp,
            type=message_type,
            user_id=user_id,
            app_id=app_id,
        )
