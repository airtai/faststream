from typing import TYPE_CHECKING, Protocol

from faststream.broker.types import MsgType

if TYPE_CHECKING:
    from faststream.broker.message import StreamMessage
    from faststream.types import AnyDict


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

    def get_publish_attrs_from_kwargs(
        self,
        kwargs: "AnyDict",
    ) -> "AnyDict": ...

    def get_publish_destination_name(
        self,
        kwargs: "AnyDict",
    ) -> str: ...
