from typing import TYPE_CHECKING, Protocol, TypedDict

from faststream.broker.message import MsgType, StreamMessage

if TYPE_CHECKING:
    from faststream.broker.message import StreamMessage
    from faststream.types import AnyDict


class ConsumeAttrs(TypedDict):
    message_size: int
    destination_name: str
    messages_count: int


class PublishAttrs(TypedDict):
    destination_name: str


class MetricsSettingsProvider(Protocol[MsgType]):
    messaging_system: str

    def get_consume_attrs_from_message(
        self,
        msg: "StreamMessage[MsgType]",
    ) -> ConsumeAttrs: ...

    def get_publish_destination_name_from_kwargs(
        self,
        kwargs: "AnyDict",
    ) -> str: ...
