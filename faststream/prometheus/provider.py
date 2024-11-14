from typing import TYPE_CHECKING, Protocol

from faststream.message.message import MsgType, StreamMessage

if TYPE_CHECKING:
    from faststream.prometheus import ConsumeAttrs
    from faststream.response.response import PublishCommand


class MetricsSettingsProvider(Protocol[MsgType]):
    messaging_system: str

    def get_consume_attrs_from_message(
        self,
        msg: "StreamMessage[MsgType]",
    ) -> "ConsumeAttrs": ...

    def get_publish_destination_name_from_cmd(
        self,
        cmd: "PublishCommand",
    ) -> str: ...
