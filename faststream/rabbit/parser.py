from typing import Any, Optional, Pattern
from uuid import uuid4

import aio_pika
from aio_pika.abc import DeliveryMode

from faststream.broker.message import StreamMessage
from faststream.broker.parsers import decode_message, encode_message
from faststream.rabbit.message import RabbitMessage
from faststream.rabbit.types import AioPikaSendableMessage
from faststream.types import AnyDict, DecodedMessage
from faststream.utils.context.main import context


class AioPikaParser:
    """A class for parsing, encoding, and decoding messages using aio-pika.

    Methods:
        parse_message(message: aio_pika.IncomingMessage) -> StreamMessage[aio_pika.IncomingMessage]:
            Parses an incoming message and returns a StreamMessage object.

        decode_message(msg: StreamMessage[aio_pika.IncomingMessage]) -> DecodedMessage:
            Decodes a StreamMessage object and returns a DecodedMessage object.

        encode_message(message: AioPikaSendableMessage, persist: bool = False, callback_queue: Optional[aio_pika.abc.AbstractRobustQueue] = None, reply_to: Optional[str] = None, **message_kwargs: Any) -> aio_pika.Message:
            Encodes a message into an aio_pika.Message object.
    !!! note

        The above docstring is autogenerated by docstring-gen library (https://docstring-gen.airt.ai)
    """

    @staticmethod
    async def parse_message(
        message: aio_pika.IncomingMessage,
    ) -> StreamMessage[aio_pika.IncomingMessage]:
        """Parses an incoming message and returns a RabbitMessage object.

        Args:
            message: The incoming message to parse.

        Returns:
            A StreamMessage object representing the parsed message.
        !!! note

            The above docstring is autogenerated by docstring-gen library (https://docstring-gen.airt.ai)
        """
        handler = context.get("handler_")
        path: AnyDict = {}
        if handler and (path_re := handler.queue.path_regex):
            path_re: Optional[Pattern[str]]
            if path_re is not None:
                match = path_re.match(message.routing_key or "")
                if match:
                    path = match.groupdict()

        return RabbitMessage(
            body=message.body,
            headers=message.headers,
            reply_to=message.reply_to or "",
            content_type=message.content_type,
            message_id=message.message_id or str(uuid4()),
            correlation_id=message.correlation_id or str(uuid4()),
            path=path,
            raw_message=message,
        )

    @staticmethod
    async def decode_message(
        msg: StreamMessage[aio_pika.IncomingMessage],
    ) -> DecodedMessage:
        """Decode a message.

        Args:
            msg: The message to decode.

        Returns:
            The decoded message.
        !!! note

            The above docstring is autogenerated by docstring-gen library (https://docstring-gen.airt.ai)
        """
        return decode_message(msg)

    @staticmethod
    def encode_message(
        message: AioPikaSendableMessage,
        persist: bool = False,
        callback_queue: Optional[aio_pika.abc.AbstractRobustQueue] = None,
        reply_to: Optional[str] = None,
        **message_kwargs: Any,
    ) -> aio_pika.Message:
        """Encodes a message for sending using AioPika.

        Args:
            message (AioPikaSendableMessage): The message to encode.
            persist (bool, optional): Whether to persist the message. Defaults to False.
            callback_queue (aio_pika.abc.AbstractRobustQueue, optional): The callback queue to use for replies. Defaults to None.
            reply_to (str, optional): The reply-to queue to use for replies. Defaults to None.
            **message_kwargs (Any): Additional keyword arguments to include in the encoded message.

        Returns:
            aio_pika.Message: The encoded message.

        Raises:
            NotImplementedError: If the message is not an instance of aio_pika.Message.
        !!! note

            The above docstring is autogenerated by docstring-gen library (https://docstring-gen.airt.ai)
        """
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
