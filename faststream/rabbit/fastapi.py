from aio_pika import IncomingMessage

from faststream.broker.fastapi.router import StreamRouter
from faststream.rabbit.broker import RabbitBroker


class RabbitRouter(StreamRouter[IncomingMessage]):
    broker_class = RabbitBroker
