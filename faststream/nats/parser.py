from typing import Optional, Pattern
from uuid import uuid4

from nats.aio.msg import Msg

from faststream.broker.message import StreamMessage
from faststream.broker.parsers import decode_message
from faststream.nats.message import NatsMessage
from faststream.types import AnyDict, DecodedMessage
from faststream.utils.context.main import context


class NatsParser:
    def __init__(self, is_js: bool):
        self.is_js = is_js

    async def parse_message(
        self,
        message: Msg,
    ) -> StreamMessage[Msg]:
        headers = message.header or {}

        handler = context.get("handler_")
        path: AnyDict = {}
        path_re: Optional[Pattern[str]]
        if handler and (path_re := handler.path_regex):
            if path_re is not None:
                match = path_re.match(message.subject)
                if match:
                    path = match.groupdict()

        return NatsMessage(
            is_js=self.is_js,
            raw_message=message,
            body=message.data,
            path=path,
            reply_to=headers.get("reply_to", "") if self.is_js else message.reply,
            headers=headers,
            content_type=headers.get("content-type", ""),
            message_id=headers.get("message_id", str(uuid4())),
            correlation_id=headers.get("correlation_id", str(uuid4())),
        )

    @staticmethod
    async def decode_message(
        msg: StreamMessage[Msg],
    ) -> DecodedMessage:
        return decode_message(msg)


JsParser = NatsParser(True)
Parser = NatsParser(False)
