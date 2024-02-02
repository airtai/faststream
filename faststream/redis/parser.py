from typing import TYPE_CHECKING, Optional, Sequence, Tuple, Union, Generic, TypeVar, Type, ClassVar, List
from uuid import uuid4

from pydantic import BaseModel, Field

from faststream._compat import model_parse, model_to_json, dump_json
from faststream.broker.parsers import decode_message, encode_message
from faststream.broker.message import StreamMessage
from faststream.redis.message import (
    BaseMessage,
    PubSubMessage,
    ListMessage,
    BatchListMessage,
    StreamMessage as RStreamMessage,
    BatchStreamMessage,
    RedisStreamMessage,
)
from faststream.types import AnyDict, DecodedMessage, SendableMessage
from faststream.utils.context.repository import context
from faststream.constants import ContentTypes

if TYPE_CHECKING:
    from faststream.redis.asyncapi import Handler

DATA_KEY = "__data__"
bDATA_KEY = DATA_KEY.encode()  # noqa: N816

MsgType = TypeVar("MsgType", bound=BaseMessage)


class RawMessage(BaseModel):
    """A class to represent a raw Redis message."""

    data: bytes
    headers: AnyDict = Field(default_factory=dict)

    @classmethod
    def build(
        cls,
        message: Union[Sequence[SendableMessage], SendableMessage],
        reply_to: str = "",
        headers: Optional[AnyDict] = None,
        correlation_id: Optional[str] = None,
    ) -> "RawMessage":
        payload, content_type = encode_message(message)

        headers_to_send = {
            "correlation_id": correlation_id or str(uuid4()),
        }

        if content_type:
            headers_to_send["content-type"] = content_type

        if reply_to:
            headers_to_send["reply_to"] = reply_to

        if headers is not None:
            headers_to_send.update(headers)

        return cls(
            data=payload,
            headers=headers_to_send,
        )

    @classmethod
    def encode(
        cls,
        message: Union[Sequence[SendableMessage], SendableMessage],
        reply_to: str = "",
        headers: Optional[AnyDict] = None,
        correlation_id: Optional[str] = None,
    ) -> str:
        return model_to_json(
            cls.build(
                message=message,
                reply_to=reply_to,
                headers=headers,
                correlation_id=correlation_id,
            )
        )

    @classmethod
    def parse(cls, data: bytes) -> Tuple[bytes, AnyDict]:
        try:
            obj = model_parse(cls, data)
        except Exception:
            # Raw Redis message format
            data = data
            headers: AnyDict = {}
        else:
            # FastStream message format
            data = obj.data
            headers = obj.headers

        return data, headers


class SimpleParser(Generic[MsgType]):
    msg_class: ClassVar[Type[StreamMessage[MsgType]]] = StreamMessage

    @classmethod
    async def parse_message(cls, message: MsgType) -> StreamMessage[MsgType]:
        data, headers = cls._parse_data(message)
        id_ = str(uuid4())
        return cls.msg_class(
            raw_message=message,
            body=data,
            path=cls.get_path(message),
            headers=headers,
            reply_to=headers.get("reply_to", ""),
            content_type=headers.get("content-type"),
            message_id=headers.get("message_id", id_),
            correlation_id=headers.get("correlation_id", id_),
        )

    @staticmethod
    def _parse_data(message: MsgType) -> Tuple[bytes, AnyDict]:
        return RawMessage.parse(message["data"])

    @staticmethod
    def get_path(message: MsgType) -> AnyDict:
        return {}
    
    @staticmethod
    async def decode_message(
        msg: StreamMessage[MsgType],
    ) -> DecodedMessage:
        return decode_message(msg)


class RedisPubSubParser(SimpleParser[PubSubMessage]):
    @staticmethod
    def get_path(message: PubSubMessage) -> AnyDict:
        handler: Optional["Handler"]
        if (
            message.get("pattern")
            and (handler := context.get_local("handler_"))
            and handler.channel is not None
            and (path_re := handler.channel.path_regex) is not None
            and (match := path_re.match(message["channel"])) is not None
        ):
            return match.groupdict()

        else:
            return {}


class RedisListParser(SimpleParser[ListMessage]):
    pass


class RedisBatchListParser(SimpleParser[BatchListMessage]):
    @staticmethod
    def _parse_data(message: BatchListMessage) -> Tuple[bytes, AnyDict]:
        return (
            dump_json([
                RawMessage.parse(x)[0]
                for x in message["data"]
            ]),
            {"content-type": ContentTypes.json}
        )


class RedisStreamParser(SimpleParser[RStreamMessage]):
    msg_class: ClassVar[Type[StreamMessage[MsgType]]] = RedisStreamMessage

    @classmethod
    def _parse_data(cls, message: RStreamMessage) -> Tuple[bytes, AnyDict]:
        data = message["data"]
        return RawMessage.parse(data.get(
            bDATA_KEY,
            data,
        ))

class RedisBatchStreamParser(SimpleParser[BatchStreamMessage]):
    msg_class: ClassVar[Type[StreamMessage[MsgType]]] = RedisStreamMessage

    @staticmethod
    def _parse_data(message: BatchStreamMessage) -> Tuple[bytes, AnyDict]:
        return (
            dump_json([
                RawMessage.parse(x.get(
                    bDATA_KEY,
                    x,
                ))[0]
                for x in message["data"]
            ]),
            {"content-type": ContentTypes.json}
        )