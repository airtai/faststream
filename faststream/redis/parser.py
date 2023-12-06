from typing import Optional, Pattern, Tuple, Union, overload
from uuid import uuid4

from pydantic import BaseModel, Field

from faststream._compat import dump_json, model_parse, model_to_json
from faststream.broker.parsers import decode_message, encode_message
from faststream.redis.message import (
    BatchMessage,
    BatchRedisMessage,
    OneMessage,
    OneRedisMessage,
)
from faststream.types import AnyDict, DecodedMessage, SendableMessage
from faststream.utils.context.main import context

DATA_KEY = "__data__"
bDATA_KEY = DATA_KEY.encode()


class RawMessage(BaseModel):
    data: bytes
    headers: AnyDict = Field(default_factory=dict)

    @classmethod
    def build(
        cls,
        message: SendableMessage,
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
        message: SendableMessage,
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


class RedisParser:
    @classmethod
    @overload
    async def parse_message(
        cls,
        message: OneMessage,
    ) -> OneRedisMessage:
        pass

    @classmethod
    @overload
    async def parse_message(
        cls,
        message: BatchMessage,
    ) -> BatchRedisMessage:
        pass

    @classmethod
    async def parse_message(
        cls,
        message: Union[OneMessage, BatchMessage],
    ) -> Union[OneRedisMessage, BatchRedisMessage]:
        id_ = str(uuid4())

        if message["type"] == "batch":
            data = dump_json(
                [cls.parse_one_msg(x)[0] for x in message["data"]]
            ).encode()

            return BatchRedisMessage(
                raw_message=message,
                body=data,
                content_type="application/json",
                message_id=id_,
                correlation_id=id_,
            )

        else:
            data, headers = cls.parse_one_msg(message["data"])

            channel = message.get("channel", b"").decode()

            handler = context.get_local("handler_")
            path_re: Optional[Pattern[str]]
            path: AnyDict = {}
            if (
                handler
                and handler.channel is not None
                and (path_re := handler.channel.path_regex) is not None
            ):
                if path_re is not None:
                    match = path_re.match(channel)
                    if match:
                        path = match.groupdict()

            return OneRedisMessage(
                raw_message=message,
                body=data,
                path=path,
                headers=headers,
                reply_to=headers.get("reply_to", ""),
                content_type=headers.get("content-type", ""),
                message_id=message.get("message_id", id_),
                correlation_id=headers.get("correlation_id", id_),
            )

    @staticmethod
    def parse_one_msg(raw_data: bytes) -> Tuple[bytes, AnyDict]:
        try:
            obj = model_parse(RawMessage, raw_data)
        except Exception:
            # Raw Redis message format
            data = raw_data
            headers: AnyDict = {}
        else:
            # FastStream message format
            data = obj.data
            headers = obj.headers

        return data, headers

    @staticmethod
    async def decode_message(
        msg: OneRedisMessage,
    ) -> DecodedMessage:
        return decode_message(msg)
