from faststream.rabbit.schemas.constants import ExchangeType
from faststream.rabbit.schemas.exchange import RabbitExchange
from faststream.rabbit.schemas.proto import BaseRMQInformation
from faststream.rabbit.schemas.queue import QueueType, RabbitQueue

__all__ = (
    "RABBIT_REPLY",
    "BaseRMQInformation",
    "ExchangeType",
    "QueueType",
    "RabbitExchange",
    "RabbitQueue",
)

RABBIT_REPLY = RabbitQueue("amq.rabbitmq.reply-to", passive=True)
