from typing import TYPE_CHECKING

from opentelemetry.semconv.trace import SpanAttributes

from faststream.__about__ import SERVICE_NAME
from faststream.broker.middlewares.telemetry import TelemetrySettingsProvider

if TYPE_CHECKING:
    from nats.aio.msg import Msg

    from faststream.broker.message import StreamMessage
    from faststream.types import AnyDict


class NatsTelemetrySettingsProvider(TelemetrySettingsProvider["Msg"]):
    __slots__ = ("messaging_system",)

    def __init__(self) -> None:
        self.messaging_system = "nats"

    def get_consume_attrs_from_message(
        self,
        msg: "StreamMessage[Msg]",
    ) -> "AnyDict":
        return {
            SpanAttributes.MESSAGING_SYSTEM: self.messaging_system,
            SpanAttributes.MESSAGING_MESSAGE_ID: msg.message_id,
            SpanAttributes.MESSAGING_MESSAGE_CONVERSATION_ID: msg.correlation_id,
            SpanAttributes.MESSAGING_MESSAGE_PAYLOAD_SIZE_BYTES: len(msg.body),
            "messaging.destination_publish.name": msg.raw_message.subject,
        }

    @staticmethod
    def get_consume_destination_name(
        msg: "StreamMessage[Msg]",
    ) -> str:
        return msg.raw_message.subject

    def get_publish_attrs_from_kwargs(
        self,
        kwargs: "AnyDict",
    ) -> "AnyDict":
        attrs = {
            SpanAttributes.MESSAGING_SYSTEM: self.messaging_system,
        }

        if (subject := kwargs.get("subject")) is not None:
            attrs[SpanAttributes.MESSAGING_DESTINATION_NAME] = subject
        if (correlation_id := kwargs.get("correlation_id")) is not None:
            attrs[SpanAttributes.MESSAGING_MESSAGE_CONVERSATION_ID] = correlation_id
        if (message_id := kwargs.get("message_id")) is not None:
            attrs[SpanAttributes.MESSAGING_MESSAGE_ID] = message_id

        return attrs

    @staticmethod
    def get_publish_destination_name(
        kwargs: "AnyDict",
    ) -> str:
        subject: str = kwargs.get("subject", SERVICE_NAME)
        return subject
