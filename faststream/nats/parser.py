from typing import TYPE_CHECKING, Any, List, Optional

from faststream.broker.message import StreamMessage, decode_message, gen_cor_id
from faststream.nats.message import NatsBatchMessage, NatsMessage
from faststream.utils.context.repository import context

if TYPE_CHECKING:
    from nats.aio.msg import Msg

    from faststream.nats.subscriber.usecase import LogicSubscriber
    from faststream.types import AnyDict, DecodedMessage


class NatsBaseParser:
    """A class to parse NATS messages."""

    @staticmethod
    def get_path(
        subject: str,
    ) -> Optional["AnyDict"]:
        path: Optional["AnyDict"] = None

        handler: Optional["LogicSubscriber[Any]"]
        if (
            (handler := context.get_local("handler_")) is not None
            and (path_re := handler.path_regex) is not None
            and (match := path_re.match(subject)) is not None
        ):
            path = match.groupdict()

        return path

    @staticmethod
    async def decode_message(
        msg: "StreamMessage[Msg]",
    ) -> "DecodedMessage":
        return decode_message(msg)


class NatsParser(NatsBaseParser):
    """A class to parse NATS core messages."""

    @classmethod
    async def parse_message(
        cls,
        message: "Msg",
        *,
        path: Optional["AnyDict"] = None,
    ) -> "StreamMessage[Msg]":
        if path is None:
            path = cls.get_path(message.subject)

        headers = message.header or {}

        message._ackd = True  # prevent message from acking

        return NatsMessage(
            raw_message=message,
            body=message.data,
            path=path or {},
            reply_to=message.reply,
            headers=headers,
            content_type=headers.get("content-type", ""),
            message_id=headers.get("message_id", gen_cor_id()),
            correlation_id=headers.get("correlation_id", gen_cor_id()),
        )


class JsParser(NatsBaseParser):
    """A class to parse NATS JS messages."""

    @classmethod
    async def parse_message(
        cls,
        message: "Msg",
        *,
        path: Optional["AnyDict"] = None,
    ) -> "StreamMessage[Msg]":
        if path is None:
            path = cls.get_path(message.subject)

        headers = message.header or {}

        return NatsMessage(
            raw_message=message,
            body=message.data,
            path=path or {},
            reply_to=headers.get("reply_to", ""),  # differ from core
            headers=headers,
            content_type=headers.get("content-type", ""),
            message_id=headers.get("message_id", gen_cor_id()),
            correlation_id=headers.get("correlation_id", gen_cor_id()),
        )


class BatchParser(JsParser):
    """A class to parse NATS batch messages."""

    @staticmethod
    async def parse_batch(
        message: List["Msg"],
    ) -> "StreamMessage[List[Msg]]":
        return NatsBatchMessage(
            raw_message=message,
            body=[m.data for m in message],
        )

    @classmethod
    async def decode_batch(
        cls,
        msg: "StreamMessage[List[Msg]]",
    ) -> List["DecodedMessage"]:
        data: List["DecodedMessage"] = []

        path: Optional["AnyDict"] = None
        for m in msg.raw_message:
            one_msg = await cls.parse_message(m, path=path)
            path = one_msg.path

            data.append(decode_message(one_msg))

        return data
