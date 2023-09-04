from aio_pika import IncomingMessage

from faststream.broker.fastapi.router import StreamRouter
from faststream.rabbit.broker import RabbitBroker


class RabbitRouter(StreamRouter[IncomingMessage]):
    broker_class = RabbitBroker

    @staticmethod
    def _setup_log_context(
        main_broker: RabbitBroker,
        including_broker: RabbitBroker,
    ) -> None:
        for h in including_broker.handlers.values():
            main_broker._setup_log_context(h.queue, h.exchange)
