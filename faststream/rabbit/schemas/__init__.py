from faststream.rabbit.schemas.constants import ExchangeType
from faststream.rabbit.schemas.exchange import RabbitExchange
from faststream.rabbit.schemas.proto import BaseRMQInformation
from faststream.rabbit.schemas.queue import RabbitQueue
from faststream.rabbit.schemas.reply import ReplyConfig

__all__ = (
    "ExchangeType",
    "RabbitQueue",
    "RabbitExchange",
    "ReplyConfig",
    "RABBIT_REPLY",
    "BaseRMQInformation",
)

RABBIT_REPLY = RabbitQueue("amq.rabbitmq.reply-to", passive=True)
