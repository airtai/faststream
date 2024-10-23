from typing import TYPE_CHECKING, Protocol

from faststream.broker.message import MsgType

if TYPE_CHECKING:
    from faststream.broker.message import StreamMessage
    from faststream.prometheus import ConsumeAttrs
    from faststream.types import AnyDict


class MetricsSettingsProvider(Protocol[MsgType]):
    messaging_system: str

    def get_consume_attrs_from_message(
        self,
        msg: "StreamMessage[MsgType]",
    ) -> "ConsumeAttrs": ...

    def get_publish_destination_name_from_kwargs(
        self,
        kwargs: "AnyDict",
    ) -> str: ...
