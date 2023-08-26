from typing import Any, Optional
from uuid import uuid4

import aio_pika
from aio_pika.abc import DeliveryMode

from faststream.broker.message import StreamMessage
from faststream.broker.parsers import decode_message, encode_message
from faststream.rabbit.message import RabbitMessage
from faststream.rabbit.types import AioPikaSendableMessage
from faststream.types import DecodedMessage


class AioPikaParser:
    @staticmethod
    async def parse_message(
        message: aio_pika.IncomingMessage,
    ) -> StreamMessage[aio_pika.IncomingMessage]:
        return RabbitMessage(
            body=message.body,
            headers=message.headers,
            reply_to=message.reply_to or "",
            content_type=message.content_type,
            message_id=message.message_id or str(uuid4()),
            correlation_id=message.correlation_id or str(uuid4()),
            raw_message=message,
        )

    @staticmethod
    async def decode_message(
        msg: StreamMessage[aio_pika.IncomingMessage],
    ) -> DecodedMessage:
        return decode_message(msg)

    @staticmethod
    def encode_message(
        message: AioPikaSendableMessage,
        persist: bool = False,
        callback_queue: Optional[aio_pika.abc.AbstractRobustQueue] = None,
        reply_to: Optional[str] = None,
        **message_kwargs: Any,
    ) -> aio_pika.Message:
        if not isinstance(message, aio_pika.Message):
            message, content_type = encode_message(message)

            delivery_mode = (
                DeliveryMode.PERSISTENT if persist else DeliveryMode.NOT_PERSISTENT
            )

            message = aio_pika.Message(
                message,
                **{
                    "delivery_mode": delivery_mode,
                    "content_type": content_type,
                    "reply_to": callback_queue or reply_to,
                    "correlation_id": str(uuid4()),
                    **message_kwargs,
                },
            )

        return message
