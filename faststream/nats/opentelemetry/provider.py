from typing import TYPE_CHECKING, List, Optional, Sequence, Union, overload

from opentelemetry.semconv.trace import SpanAttributes

from faststream.__about__ import SERVICE_NAME
from faststream.broker.types import MsgType
from faststream.opentelemetry import TelemetrySettingsProvider
from faststream.opentelemetry.consts import MESSAGING_DESTINATION_PUBLISH_NAME

if TYPE_CHECKING:
    from nats.aio.msg import Msg

    from faststream.broker.message import StreamMessage
    from faststream.types import AnyDict


class BaseNatsTelemetrySettingsProvider(TelemetrySettingsProvider[MsgType]):
    __slots__ = ("messaging_system",)

    def __init__(self) -> None:
        self.messaging_system = "nats"

    def get_publish_attrs_from_kwargs(
        self,
        kwargs: "AnyDict",
    ) -> "AnyDict":
        return {
            SpanAttributes.MESSAGING_SYSTEM: self.messaging_system,
            SpanAttributes.MESSAGING_DESTINATION_NAME: kwargs["subject"],
            SpanAttributes.MESSAGING_MESSAGE_CONVERSATION_ID: kwargs["correlation_id"],
        }

    @staticmethod
    def get_publish_destination_name(
        kwargs: "AnyDict",
    ) -> str:
        subject: str = kwargs.get("subject", SERVICE_NAME)
        return subject


class NatsTelemetrySettingsProvider(BaseNatsTelemetrySettingsProvider["Msg"]):
    def get_consume_attrs_from_message(
        self,
        msg: "StreamMessage[Msg]",
    ) -> "AnyDict":
        return {
            SpanAttributes.MESSAGING_SYSTEM: self.messaging_system,
            SpanAttributes.MESSAGING_MESSAGE_ID: msg.message_id,
            SpanAttributes.MESSAGING_MESSAGE_CONVERSATION_ID: msg.correlation_id,
            SpanAttributes.MESSAGING_MESSAGE_PAYLOAD_SIZE_BYTES: len(msg.body),
            MESSAGING_DESTINATION_PUBLISH_NAME: msg.raw_message.subject,
        }

    @staticmethod
    def get_consume_destination_name(
        msg: "StreamMessage[Msg]",
    ) -> str:
        return msg.raw_message.subject


class NatsBatchTelemetrySettingsProvider(
    BaseNatsTelemetrySettingsProvider[List["Msg"]]
):
    def get_consume_attrs_from_message(
        self,
        msg: "StreamMessage[List[Msg]]",
    ) -> "AnyDict":
        return {
            SpanAttributes.MESSAGING_SYSTEM: self.messaging_system,
            SpanAttributes.MESSAGING_MESSAGE_ID: msg.message_id,
            SpanAttributes.MESSAGING_MESSAGE_CONVERSATION_ID: msg.correlation_id,
            SpanAttributes.MESSAGING_MESSAGE_PAYLOAD_SIZE_BYTES: len(msg.body),
            SpanAttributes.MESSAGING_BATCH_MESSAGE_COUNT: len(msg.raw_message),
            MESSAGING_DESTINATION_PUBLISH_NAME: msg.raw_message[0].subject,
        }

    @staticmethod
    def get_consume_destination_name(
        msg: "StreamMessage[List[Msg]]",
    ) -> str:
        return msg.raw_message[0].subject


@overload
def telemetry_attributes_provider_factory(
    msg: Optional["Msg"],
) -> NatsTelemetrySettingsProvider: ...


@overload
def telemetry_attributes_provider_factory(
    msg: Sequence["Msg"],
) -> NatsBatchTelemetrySettingsProvider: ...


@overload
def telemetry_attributes_provider_factory(
    msg: Union["Msg", Sequence["Msg"], None],
) -> Union[
    NatsTelemetrySettingsProvider,
    NatsBatchTelemetrySettingsProvider,
]: ...


def telemetry_attributes_provider_factory(
    msg: Union["Msg", Sequence["Msg"], None],
) -> Union[
    NatsTelemetrySettingsProvider,
    NatsBatchTelemetrySettingsProvider,
]:
    if isinstance(msg, Sequence):
        return NatsBatchTelemetrySettingsProvider()
    else:
        return NatsTelemetrySettingsProvider()
