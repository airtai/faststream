from typing import TYPE_CHECKING, Sequence, Tuple, Union

from faststream.broker.message import MsgType, StreamMessage
from faststream.prometheus.provider import (
    ConsumeAttrs,
    MetricsSettingsProvider,
)

if TYPE_CHECKING:
    from aiokafka import ConsumerRecord

    from faststream.types import AnyDict


class BaseKafkaMetricsSettingsProvider(MetricsSettingsProvider[MsgType]):
    def __init__(self):
        self.messaging_system = "kafka"

    def get_publish_destination_name_from_kwargs(
        self,
        kwargs: "AnyDict",
    ) -> str:
        return kwargs["topic"]


class KafkaMetricsSettingsProvider(BaseKafkaMetricsSettingsProvider["ConsumerRecord"]):
    def get_consume_attrs_from_message(
        self,
        msg: "StreamMessage[ConsumerRecord]",
    ) -> ConsumeAttrs:
        return {
            "destination_name": msg.raw_message.topic,
            "message_size": len(msg.body),
            "messages_count": 1,
        }


class BatchKafkaMetricsSettingsProvider(
    BaseKafkaMetricsSettingsProvider[Tuple["ConsumerRecord", ...]]
):
    def get_consume_attrs_from_message(
        self,
        msg: "StreamMessage[Tuple[ConsumerRecord, ...]]",
    ) -> ConsumeAttrs:
        raw_message = msg.raw_message[0]
        return {
            "destination_name": raw_message.topic,
            "message_size": len(bytearray().join(msg.body)),
            "messages_count": len(msg.raw_message),
        }


def settings_provider_factory(
    msg: Union["ConsumerRecord", Sequence["ConsumerRecord"], None],
) -> Union[
    KafkaMetricsSettingsProvider,
    BatchKafkaMetricsSettingsProvider,
]:
    if isinstance(msg, Sequence):
        return BatchKafkaMetricsSettingsProvider()
    else:
        return KafkaMetricsSettingsProvider()
