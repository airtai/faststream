from typing import TYPE_CHECKING, Protocol

from faststream._internal.types import MsgType

if TYPE_CHECKING:
    from faststream._internal.basic_types import AnyDict
    from faststream.message import StreamMessage
    from faststream.response.response import PublishCommand


class TelemetrySettingsProvider(Protocol[MsgType]):
    messaging_system: str

    def get_consume_attrs_from_message(
        self,
        msg: "StreamMessage[MsgType]",
    ) -> "AnyDict": ...

    def get_consume_destination_name(
        self,
        msg: "StreamMessage[MsgType]",
    ) -> str: ...

    def get_publish_attrs_from_cmd(
        self,
        cmd: "PublishCommand",
    ) -> "AnyDict": ...

    def get_publish_destination_name(
        self,
        cmd: "PublishCommand",
    ) -> str: ...
