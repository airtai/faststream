import json
from typing import Optional, Pattern, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field

from faststream._compat import dump_json, model_parse, model_to_json
from faststream.broker.message import StreamMessage
from faststream.broker.parsers import decode_message, encode_message
from faststream.redis.message import PubSubMessage, RedisMessage
from faststream.types import AnyDict, DecodedMessage, SendableMessage
from faststream.utils.context.main import context

DATA_KEY = "data"
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
    async def parse_message(
        cls, message: PubSubMessage,
    ) -> StreamMessage[PubSubMessage]:
        path: AnyDict = {}
        if message["type"] == "batch":
            data = dump_json([
                cls._parse_one_msg(x)[0]
                for x in message["data"]
            ]).encode()
            headers = {
                "content-type": "application/json"
            }
        else:
            data, headers = cls._parse_one_msg(message["data"])

            channel = message.get("channel", b"").decode()

            handler = context.get_local("handler_")
            path_re: Optional[Pattern[str]]
            if (
                handler
                and handler.channel is not None
                and (path_re := handler.channel.path_regex) is not None
            ):
                if path_re is not None:
                    match = path_re.match(channel)
                    if match:
                        path = match.groupdict()

        return RedisMessage(
            raw_message=message,
            body=data,
            path=path,
            headers=headers,
            reply_to=headers.get("reply_to", ""),
            content_type=headers.get("content-type", ""),
            message_id=message.get("message_id", str(uuid4())),
            correlation_id=headers.get("correlation_id", str(uuid4())),
        )

    @staticmethod
    def _parse_one_msg(
        raw_data: bytes
    ) -> Tuple[bytes, AnyDict]:
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
        msg: StreamMessage[PubSubMessage],
    ) -> DecodedMessage:
        return decode_message(msg)
