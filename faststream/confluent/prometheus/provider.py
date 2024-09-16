from typing import TYPE_CHECKING, Sequence, Tuple, Union

from faststream.broker.message import MsgType, StreamMessage
from faststream.prometheus.provider import (
    ConsumeAttrs,
    MetricsSettingsProvider,
)

if TYPE_CHECKING:
    from confluent_kafka import Message

    from faststream.types import AnyDict


class BaseConfluentMetricsSettingsProvider(MetricsSettingsProvider[MsgType]):
    def __init__(self):
        self.messaging_system = "kafka"

    def get_publish_destination_name_from_kwargs(
        self,
        kwargs: "AnyDict",
    ) -> str:
        return kwargs["topic"]


class ConfluentMetricsSettingsProvider(BaseConfluentMetricsSettingsProvider["Message"]):
    def get_consume_attrs_from_message(
        self,
        msg: "StreamMessage[Message]",
    ) -> ConsumeAttrs:
        return {
            "destination_name": msg.raw_message.topic(),
            "message_size": len(msg.body),
            "messages_count": 1,
        }


class BatchConfluentMetricsSettingsProvider(
    BaseConfluentMetricsSettingsProvider[Tuple["Message", ...]]
):
    def get_consume_attrs_from_message(
        self,
        msg: "StreamMessage[Tuple[Message, ...]]",
    ) -> ConsumeAttrs:
        raw_message = msg.raw_message[0]
        return {
            "destination_name": raw_message.topic(),
            "message_size": len(bytearray().join(msg.body)),
            "messages_count": len(msg.raw_message),
        }


def settings_provider_factory(
    msg: Union["Message", Sequence["Message"], None],
) -> Union[
    ConfluentMetricsSettingsProvider,
    BatchConfluentMetricsSettingsProvider,
]:
    if isinstance(msg, Sequence):
        return BatchConfluentMetricsSettingsProvider()
    else:
        return ConfluentMetricsSettingsProvider()
