from typing import List, Optional, Pattern, Union, overload
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

    @overload
    async def parse_message(
        self, message: List[Msg], *, path: Optional[AnyDict] = None
    ) -> StreamMessage[List[Msg]]:
        ...

    @overload
    async def parse_message(
        self, message: Msg, *, path: Optional[AnyDict] = None
    ) -> StreamMessage[Msg]:
        ...

    async def parse_message(
        self, message: Union[Msg, List[Msg]], *, path: Optional[AnyDict] = None
    ) -> Union[StreamMessage[Msg], StreamMessage[List[Msg]],]:
        if isinstance(message, list):
            return NatsMessage(
                is_js=self.is_js,
                raw_message=message,  # type: ignore[arg-type]
                body=[m.data for m in message],
            )

        else:
            path_re: Optional[Pattern[str]]
            if (
                path is None
                and (handler := context.get_local("handler_"))
                and (path_re := handler.path_regex) is not None
                and (match := path_re.match(message.subject)) is not None
            ):
                path = match.groupdict()

            headers = message.header or {}

            return NatsMessage(
                is_js=self.is_js,
                raw_message=message,
                body=message.data,
                path=path or {},
                reply_to=headers.get("reply_to", "") if self.is_js else message.reply,
                headers=headers,
                content_type=headers.get("content-type", ""),
                message_id=headers.get("message_id", str(uuid4())),
                correlation_id=headers.get("correlation_id", str(uuid4())),
            )

    async def decode_message(
        self,
        msg: Union[
            StreamMessage[Msg],
            StreamMessage[List[Msg]],
        ],
    ) -> DecodedMessage:
        if isinstance(msg.raw_message, list):
            data = []

            path: Optional[AnyDict] = None
            for m in msg.raw_message:
                msg = await self.parse_message(m, path=path)
                path = msg.path

                data.append(decode_message(msg))

            return data

        else:
            return decode_message(msg)


JsParser = NatsParser(True)
Parser = NatsParser(False)
