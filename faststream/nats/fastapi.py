from nats.aio.msg import Msg

from faststream.broker.fastapi.router import StreamRouter
from faststream.nats.broker import NatsBroker


class NatsRouter(StreamRouter[Msg]):
    broker_class = NatsBroker

    @staticmethod
    def _setup_log_context(
        main_broker: NatsBroker,
        including_broker: NatsBroker,
    ) -> None:
        for h in including_broker.handlers.values():
            main_broker._setup_log_context(queue=h.queue, subject=h.subject)
