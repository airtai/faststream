from typing import (
    TYPE_CHECKING,
    Any,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from faststream._compat import dump_json, json_loads
from faststream.broker.message import (
    decode_message,
    encode_message,
    gen_cor_id,
)
from faststream.constants import ContentTypes
from faststream.redis.message import (
    RedisBatchListMessage,
    RedisBatchStreamMessage,
    RedisListMessage,
    RedisMessage,
    RedisStreamMessage,
    bDATA_KEY,
)
from faststream.types import AnyDict, DecodedMessage, SendableMessage

if TYPE_CHECKING:
    from re import Pattern

    from faststream.broker.message import StreamMessage


MsgType = TypeVar("MsgType", bound=Mapping[str, Any])


class RawMessage:
    """A class to represent a raw Redis message."""

    __slots__ = (
        "data",
        "headers",
    )

    def __init__(
        self,
        data: bytes,
        headers: Optional["AnyDict"] = None,
    ) -> None:
        self.data = data
        self.headers = headers or {}

    @classmethod
    def build(
        cls,
        *,
        message: Union[Sequence["SendableMessage"], "SendableMessage"],
        reply_to: Optional[str],
        headers: Optional["AnyDict"],
        correlation_id: str,
    ) -> "RawMessage":
        payload, content_type = encode_message(message)

        headers_to_send = {
            "correlation_id": correlation_id,
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
        *,
        message: Union[Sequence["SendableMessage"], "SendableMessage"],
        reply_to: Optional[str],
        headers: Optional["AnyDict"],
        correlation_id: str,
    ) -> bytes:
        msg = cls.build(
            message=message,
            reply_to=reply_to,
            headers=headers,
            correlation_id=correlation_id,
        )

        return dump_json(
            {
                "data": msg.data,
                "headers": msg.headers,
            }
        )

    @staticmethod
    def parse(data: bytes) -> Tuple[bytes, "AnyDict"]:
        headers: "AnyDict"

        try:
            # FastStream message format
            parsed_data = json_loads(data)
            data = parsed_data["data"].encode()
            headers = parsed_data["headers"]

        except Exception:
            # Raw Redis message format
            data = data
            headers = {}

        return data, headers


class SimpleParser:
    msg_class: Type["StreamMessage[Any]"]

    def __init__(
        self,
        pattern: Optional["Pattern[str]"] = None,
    ) -> None:
        self.pattern = pattern

    async def parse_message(
        self,
        message: Mapping[str, Any],
    ) -> "StreamMessage[Mapping[str, Any]]":
        data, headers = self._parse_data(message)
        id_ = gen_cor_id()
        return self.msg_class(
            raw_message=message,
            body=data,
            path=self.get_path(message),
            headers=headers,
            reply_to=headers.get("reply_to", ""),
            content_type=headers.get("content-type"),
            message_id=headers.get("message_id", id_),
            correlation_id=headers.get("correlation_id", id_),
        )

    @staticmethod
    def _parse_data(message: Mapping[str, Any]) -> Tuple[bytes, "AnyDict"]:
        return RawMessage.parse(message["data"])

    def get_path(self, message: Mapping[str, Any]) -> "AnyDict":
        if (
            message.get("pattern")
            and (path_re := self.pattern)
            and (match := path_re.match(message["channel"]))
        ):
            return match.groupdict()

        else:
            return {}

    @staticmethod
    async def decode_message(
        msg: "StreamMessage[MsgType]",
    ) -> DecodedMessage:
        return decode_message(msg)


class RedisPubSubParser(SimpleParser):
    msg_class = RedisMessage


class RedisListParser(SimpleParser):
    msg_class = RedisListMessage


class RedisBatchListParser(SimpleParser):
    msg_class = RedisBatchListMessage

    @staticmethod
    def _parse_data(message: Mapping[str, Any]) -> Tuple[bytes, "AnyDict"]:
        return (
            dump_json(_decode_batch_body_item(x) for x in message["data"]),
            {"content-type": ContentTypes.json},
        )


class RedisStreamParser(SimpleParser):
    msg_class = RedisStreamMessage

    @classmethod
    def _parse_data(cls, message: Mapping[str, Any]) -> Tuple[bytes, "AnyDict"]:
        data = message["data"]
        return RawMessage.parse(data.get(bDATA_KEY) or dump_json(data))


class RedisBatchStreamParser(SimpleParser):
    msg_class = RedisBatchStreamMessage

    @staticmethod
    def _parse_data(message: Mapping[str, Any]) -> Tuple[bytes, "AnyDict"]:
        return (
            dump_json(
                _decode_batch_body_item(x.get(bDATA_KEY, x)) for x in message["data"]
            ),
            {"content-type": ContentTypes.json},
        )


def _decode_batch_body_item(msg_content: bytes) -> Any:
    msg_body, _ = RawMessage.parse(msg_content)
    try:
        return json_loads(msg_body)
    except Exception:
        return msg_body
