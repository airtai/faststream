from typing import TYPE_CHECKING, Optional, Sequence, Tuple, Union, overload

from opentelemetry.semconv.trace import SpanAttributes

from faststream.broker.types import MsgType
from faststream.opentelemetry import TelemetrySettingsProvider

if TYPE_CHECKING:
    from aiokafka import ConsumerRecord

    from faststream.broker.message import StreamMessage
    from faststream.types import AnyDict


class BaseKafkaTelemetrySettingsProvider(TelemetrySettingsProvider[MsgType]):
    __slots__ = ("messaging_system",)

    def __init__(self) -> None:
        self.messaging_system = "kafka"

    def get_publish_attrs_from_kwargs(
        self,
        kwargs: "AnyDict",
    ) -> "AnyDict":
        attrs = {
            SpanAttributes.MESSAGING_SYSTEM: self.messaging_system,
            SpanAttributes.MESSAGING_DESTINATION_NAME: kwargs["topic"],
            SpanAttributes.MESSAGING_MESSAGE_CONVERSATION_ID: kwargs["correlation_id"],
        }

        if (partition := kwargs.get("partition")) is not None:
            attrs[SpanAttributes.MESSAGING_KAFKA_DESTINATION_PARTITION] = partition

        if (key := kwargs.get("key")) is not None:
            attrs[SpanAttributes.MESSAGING_KAFKA_MESSAGE_KEY] = key

        return attrs

    @staticmethod
    def get_publish_destination_name(
        kwargs: "AnyDict",
    ) -> str:
        return kwargs["topic"]


class KafkaTelemetrySettingsProvider(
    BaseKafkaTelemetrySettingsProvider["ConsumerRecord"]
):
    def get_consume_attrs_from_message(
        self,
        msg: "StreamMessage[ConsumerRecord]",
    ) -> "AnyDict":
        attrs = {
            SpanAttributes.MESSAGING_SYSTEM: self.messaging_system,
            SpanAttributes.MESSAGING_MESSAGE_ID: msg.message_id,
            SpanAttributes.MESSAGING_MESSAGE_CONVERSATION_ID: msg.correlation_id,
            SpanAttributes.MESSAGING_MESSAGE_PAYLOAD_SIZE_BYTES: len(msg.body),
            SpanAttributes.MESSAGING_KAFKA_DESTINATION_PARTITION: msg.raw_message.partition,
            SpanAttributes.MESSAGING_KAFKA_MESSAGE_OFFSET: msg.raw_message.offset,
            "messaging.destination_publish.name": msg.raw_message.topic,
        }

        if msg.raw_message.key is not None:
            attrs[SpanAttributes.MESSAGING_KAFKA_MESSAGE_KEY] = msg.raw_message.key

        return attrs

    @staticmethod
    def get_consume_destination_name(
        msg: "StreamMessage[ConsumerRecord]",
    ) -> str:
        return msg.raw_message.topic


class BatchKafkaTelemetrySettingsProvider(
    BaseKafkaTelemetrySettingsProvider[Tuple["ConsumerRecord", ...]]
):
    def get_consume_attrs_from_message(
        self,
        msg: "StreamMessage[Tuple[ConsumerRecord, ...]]",
    ) -> "AnyDict":
        raw_message = msg.raw_message[0]

        attrs = {
            SpanAttributes.MESSAGING_SYSTEM: self.messaging_system,
            SpanAttributes.MESSAGING_MESSAGE_ID: msg.message_id,
            SpanAttributes.MESSAGING_MESSAGE_CONVERSATION_ID: msg.correlation_id,
            SpanAttributes.MESSAGING_MESSAGE_PAYLOAD_SIZE_BYTES: len(
                bytearray().join(msg.body)
            ),
            SpanAttributes.MESSAGING_BATCH_MESSAGE_COUNT: len(msg.raw_message),
            SpanAttributes.MESSAGING_KAFKA_DESTINATION_PARTITION: raw_message.partition,
            "messaging.destination_publish.name": raw_message.topic,
        }

        return attrs

    @staticmethod
    def get_consume_destination_name(
        msg: "StreamMessage[Tuple[ConsumerRecord, ...]]",
    ) -> str:
        return msg.raw_message[0].topic


@overload
def telemetry_attributes_provider_factory(
    msg: Optional["ConsumerRecord"],
) -> KafkaTelemetrySettingsProvider: ...


@overload
def telemetry_attributes_provider_factory(
    msg: Sequence["ConsumerRecord"],
) -> BatchKafkaTelemetrySettingsProvider: ...


@overload
def telemetry_attributes_provider_factory(
    msg: Union["ConsumerRecord", Sequence["ConsumerRecord"], None],
) -> Union[
    KafkaTelemetrySettingsProvider,
    BatchKafkaTelemetrySettingsProvider,
]: ...


def telemetry_attributes_provider_factory(
    msg: Union["ConsumerRecord", Sequence["ConsumerRecord"], None],
) -> Union[
    KafkaTelemetrySettingsProvider,
    BatchKafkaTelemetrySettingsProvider,
]:
    if isinstance(msg, Sequence):
        return BatchKafkaTelemetrySettingsProvider()
    else:
        return KafkaTelemetrySettingsProvider()
