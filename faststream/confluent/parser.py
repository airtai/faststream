from typing import TYPE_CHECKING, List, Optional, Tuple
from uuid import uuid4

from confluent_kafka import Message

from faststream.broker.message import StreamMessage
from faststream.broker.parsers import decode_message
from faststream.confluent.message import FAKE_CONSUMER, KafkaMessage
from faststream.types import DecodedMessage
from faststream.utils.context.repository import context

if TYPE_CHECKING:
    from faststream.confluent.asyncapi import Handler


class AsyncConfluentParser:
    """A class to parse Kafka messages."""

    @staticmethod
    async def parse_message(
        message: Message,
    ) -> StreamMessage[Message]:
        """Parses a Kafka message.

        Args:
            message: The Kafka message to parse.

        Returns:
            A StreamMessage object representing the parsed message.

        """
        headers = {}
        if message.headers() is not None:
            for i, j in message.headers():  # type: ignore[union-attr]
                if isinstance(j, str):
                    headers[i] = j
                else:
                    headers[i] = j.decode()
        body = message.value()
        offset = message.offset()
        _, timestamp = message.timestamp()

        handler: Optional["Handler"] = context.get_local("handler_")
        return KafkaMessage(
            body=body,
            headers=headers,
            reply_to=headers.get("reply_to", ""),
            content_type=headers.get("content-type"),
            message_id=f"{offset}-{timestamp}",
            correlation_id=headers.get("correlation_id", str(uuid4())),
            raw_message=message,
            consumer=getattr(handler, "consumer", None) or FAKE_CONSUMER,
            is_manual=getattr(handler, "is_manual", True),
        )

    @staticmethod
    async def parse_message_batch(
        message: Tuple[Message, ...],
    ) -> KafkaMessage:
        """Parses a batch of messages from a Kafka consumer.

        Args:
            message : A tuple of ConsumerRecord or Message objects representing the messages to parse.

        Returns:
            A StreamMessage object containing the parsed messages.

        Raises:
            NotImplementedError: If any of the messages are silent (i.e., have no sound).

        Static Method:
            This method is a static method. It does not require an instance of the class to be called.

        """
        first = message[0]
        last = message[-1]

        headers = {}
        if first.headers() is not None:
            for i, j in first.headers():  # type: ignore[union-attr]
                if isinstance(j, str):
                    headers[i] = j
                else:
                    headers[i] = j.decode()
        body = [m.value() for m in message]
        first_offset = first.offset()
        last_offset = last.offset()
        _, first_timestamp = first.timestamp()

        handler: Optional["Handler"] = context.get_local("handler_")
        return KafkaMessage(
            body=body,
            headers=headers,
            reply_to=headers.get("reply_to", ""),
            content_type=headers.get("content-type"),
            message_id=f"{first_offset}-{last_offset}-{first_timestamp}",
            correlation_id=headers.get("correlation_id", str(uuid4())),
            raw_message=message,
            consumer=getattr(handler, "consumer", None) or FAKE_CONSUMER,
            is_manual=getattr(handler, "is_manual", True),
        )

    @staticmethod
    async def decode_message(msg: StreamMessage[Message]) -> DecodedMessage:
        """Decodes a message.

        Args:
            msg: The message to be decoded.

        Returns:
            The decoded message.

        """
        return decode_message(msg)

    @classmethod
    async def decode_message_batch(
        cls, msg: StreamMessage[Tuple[Message, ...]]
    ) -> List[DecodedMessage]:
        """Decode a batch of messages.

        Args:
            msg: A stream message containing a tuple of consumer records.

        Returns:
            A list of decoded messages.

        """
        return [decode_message(await cls.parse_message(m)) for m in msg.raw_message]
