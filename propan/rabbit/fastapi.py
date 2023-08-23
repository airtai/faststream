from aio_pika import IncomingMessage

from propan.broker.fastapi.router import PropanRouter
from propan.rabbit.broker import RabbitBroker


class RabbitRouter(PropanRouter[IncomingMessage]):
    broker_class = RabbitBroker
