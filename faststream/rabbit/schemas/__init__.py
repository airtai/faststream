from faststream.rabbit.schemas.constants import ExchangeType
from faststream.rabbit.schemas.schemas import RabbitExchange, RabbitQueue, ReplyConfig

__all__ = (
    "ExchangeType",
    "RabbitQueue",
    "RabbitExchange",
    "ReplyConfig",
    "RABBIT_REPLY",
)

RABBIT_REPLY = RabbitQueue("amq.rabbitmq.reply-to", passive=True)
