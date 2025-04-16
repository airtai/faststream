from collections.abc import Sequence
from typing import TYPE_CHECKING, Union, cast

from opentelemetry.semconv.trace import SpanAttributes

from faststream._internal.types import MsgType
from faststream.opentelemetry import TelemetrySettingsProvider
from faststream.opentelemetry.consts import MESSAGING_DESTINATION_PUBLISH_NAME

if TYPE_CHECKING:
    from confluent_kafka import Message

    from faststream._internal.basic_types import AnyDict
    from faststream.confluent.response import KafkaPublishCommand
    from faststream.message import StreamMessage
    from faststream.response import PublishCommand


class BaseConfluentTelemetrySettingsProvider(TelemetrySettingsProvider[MsgType]):
    __slots__ = ("messaging_system",)

    def __init__(self) -> None:
        self.messaging_system = "kafka"

    def get_publish_attrs_from_cmd(
        self,
        cmd: "KafkaPublishCommand",
    ) -> "AnyDict":
        attrs: AnyDict = {
            SpanAttributes.MESSAGING_SYSTEM: self.messaging_system,
            SpanAttributes.MESSAGING_DESTINATION_NAME: cmd.destination,
            SpanAttributes.MESSAGING_MESSAGE_CONVERSATION_ID: cmd.correlation_id,
        }

        if cmd.partition is not None:
            attrs[SpanAttributes.MESSAGING_KAFKA_DESTINATION_PARTITION] = cmd.partition

        if cmd.key is not None:
            attrs[SpanAttributes.MESSAGING_KAFKA_MESSAGE_KEY] = cmd.key

        return attrs

    def get_publish_destination_name(
        self,
        cmd: "PublishCommand",
    ) -> str:
        return cmd.destination


class ConfluentTelemetrySettingsProvider(
    BaseConfluentTelemetrySettingsProvider["Message"],
):
    def get_consume_attrs_from_message(
        self,
        msg: "StreamMessage[Message]",
    ) -> "AnyDict":
        attrs = {
            SpanAttributes.MESSAGING_SYSTEM: self.messaging_system,
            SpanAttributes.MESSAGING_MESSAGE_ID: msg.message_id,
            SpanAttributes.MESSAGING_MESSAGE_CONVERSATION_ID: msg.correlation_id,
            SpanAttributes.MESSAGING_MESSAGE_PAYLOAD_SIZE_BYTES: len(msg.body),
            SpanAttributes.MESSAGING_KAFKA_DESTINATION_PARTITION: msg.raw_message.partition(),
            SpanAttributes.MESSAGING_KAFKA_MESSAGE_OFFSET: msg.raw_message.offset(),
            MESSAGING_DESTINATION_PUBLISH_NAME: msg.raw_message.topic(),
        }

        if (key := msg.raw_message.key()) is not None:
            attrs[SpanAttributes.MESSAGING_KAFKA_MESSAGE_KEY] = key

        return attrs

    def get_consume_destination_name(
        self,
        msg: "StreamMessage[Message]",
    ) -> str:
        return cast("str", msg.raw_message.topic())


class BatchConfluentTelemetrySettingsProvider(
    BaseConfluentTelemetrySettingsProvider[tuple["Message", ...]],
):
    def get_consume_attrs_from_message(
        self,
        msg: "StreamMessage[tuple[Message, ...]]",
    ) -> "AnyDict":
        raw_message = msg.raw_message[0]
        return {
            SpanAttributes.MESSAGING_SYSTEM: self.messaging_system,
            SpanAttributes.MESSAGING_MESSAGE_ID: msg.message_id,
            SpanAttributes.MESSAGING_MESSAGE_CONVERSATION_ID: msg.correlation_id,
            SpanAttributes.MESSAGING_BATCH_MESSAGE_COUNT: len(msg.raw_message),
            SpanAttributes.MESSAGING_MESSAGE_PAYLOAD_SIZE_BYTES: len(
                bytearray().join(cast("Sequence[bytes]", msg.body))
            ),
            SpanAttributes.MESSAGING_KAFKA_DESTINATION_PARTITION: raw_message.partition(),
            MESSAGING_DESTINATION_PUBLISH_NAME: raw_message.topic(),
        }

    def get_consume_destination_name(
        self,
        msg: "StreamMessage[tuple[Message, ...]]",
    ) -> str:
        return cast("str", msg.raw_message[0].topic())


def telemetry_attributes_provider_factory(
    msg: Union["Message", Sequence["Message"], None],
) -> Union[
    ConfluentTelemetrySettingsProvider,
    BatchConfluentTelemetrySettingsProvider,
]:
    if isinstance(msg, Sequence):
        return BatchConfluentTelemetrySettingsProvider()
    return ConfluentTelemetrySettingsProvider()
