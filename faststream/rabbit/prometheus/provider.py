from typing import TYPE_CHECKING, Union

from faststream.prometheus.provider import (
    ConsumeAttrs,
    MetricsSettingsProvider,
)

if TYPE_CHECKING:
    from aio_pika import IncomingMessage

    from faststream.broker.message import StreamMessage
    from faststream.rabbit.schemas.exchange import RabbitExchange
    from faststream.types import AnyDict


class RabbitMetricsSettingsProvider(MetricsSettingsProvider["IncomingMessage"]):
    def __init__(self):
        self.messaging_system = "rabbitmq"

    def get_consume_attrs_from_message(
        self,
        msg: "StreamMessage[IncomingMessage]",
    ) -> ConsumeAttrs:
        exchange = msg.raw_message.exchange or "default"
        routing_key = msg.raw_message.routing_key

        return {
            "destination_name": f"{exchange}.{routing_key}",
            "messages_sizes": [len(msg.body)],
        }

    def get_publish_destination_name_from_kwargs(
        self,
        kwargs: "AnyDict",
    ) -> str:
        exchange: Union[None, str, RabbitExchange] = kwargs["exchange"]
        exchange_prefix = getattr(exchange, "name", exchange or "default")

        routing_key: str = kwargs["routing_key"]

        return f"{exchange_prefix}.{routing_key}"
