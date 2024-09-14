from typing import TYPE_CHECKING, Protocol, Sequence, TypedDict

from faststream.broker.message import MsgType, StreamMessage

if TYPE_CHECKING:
    from faststream.broker.message import StreamMessage
    from faststream.types import AnyDict


class ConsumeAttrs(TypedDict):
    messages_sizes: Sequence[int]
    destination_name: str


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
