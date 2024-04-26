from typing import TYPE_CHECKING

from opentelemetry.semconv.trace import SpanAttributes

from faststream.broker.middlewares.telemetry import TelemetrySettingsProvider

if TYPE_CHECKING:
    from aio_pika import IncomingMessage

    from faststream.broker.message import StreamMessage
    from faststream.types import AnyDict


class RabbitTelemetrySettingsProvider(TelemetrySettingsProvider["IncomingMessage"]):
    __slots__ = ("messaging_system",)

    def __init__(self) -> None:
        self.messaging_system = "rabbitmq"

    def get_consume_attrs_from_message(
        self,
        msg: "StreamMessage[IncomingMessage]",
    ) -> "AnyDict":
        return {
            SpanAttributes.MESSAGING_SYSTEM: self.messaging_system,
            SpanAttributes.MESSAGING_MESSAGE_ID: msg.message_id,
            SpanAttributes.MESSAGING_MESSAGE_CONVERSATION_ID: msg.correlation_id,
            SpanAttributes.MESSAGING_MESSAGE_PAYLOAD_SIZE_BYTES: len(msg.body),
            SpanAttributes.MESSAGING_RABBITMQ_DESTINATION_ROUTING_KEY: msg.raw_message.routing_key,
            "messaging.rabbitmq.message.delivery_tag": msg.raw_message.delivery_tag,
            "messaging.destination_publish.name": msg.raw_message.exchange,
        }

    @staticmethod
    def get_consume_destination_name(
        msg: "StreamMessage[IncomingMessage]",
    ) -> str:
        exchange = msg.raw_message.exchange or "default"
        routing_key = msg.raw_message.routing_key or "default"
        return f"{exchange}.{routing_key}"

    def get_publish_attrs_from_kwargs(
        self,
        kwargs: "AnyDict",
    ) -> "AnyDict":
        attrs = {
            SpanAttributes.MESSAGING_SYSTEM: self.messaging_system,
            SpanAttributes.MESSAGING_DESTINATION_NAME: kwargs.get("exchange") or "",
            SpanAttributes.MESSAGING_RABBITMQ_DESTINATION_ROUTING_KEY: kwargs.get("routing_key") or "",
        }

        if (correlation_id := kwargs.get("correlation_id")) is not None:
            attrs[SpanAttributes.MESSAGING_MESSAGE_CONVERSATION_ID] = correlation_id
        if (message_id := kwargs.get("message_id")) is not None:
            attrs[SpanAttributes.MESSAGING_MESSAGE_ID] = message_id
        if (delivery_tag := kwargs.get("delivery_tag")) is not None:
            attrs["messaging.rabbitmq.message.delivery_tag"] = delivery_tag

        return attrs

    @staticmethod
    def get_publish_destination_name(
        kwargs: "AnyDict",
    ) -> str:
        exchange: str = kwargs.get("exchange") or "default"
        routing_key: str = kwargs.get("routing_key") or "default"
        return f"{exchange}.{routing_key}"
