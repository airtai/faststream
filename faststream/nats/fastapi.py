from nats.aio.msg import Msg

from faststream._compat import override
from faststream.broker.fastapi.router import StreamRouter
from faststream.nats.broker import NatsBroker


class NatsRouter(StreamRouter[Msg]):
    broker_class = NatsBroker

    @override
    @staticmethod
    def _setup_log_context(  # type: ignore[override]
        main_broker: NatsBroker,
        including_broker: NatsBroker,
    ) -> None:
        for h in including_broker.handlers.values():
            main_broker._setup_log_context(
                queue=h.queue,
                subject=h.subject,
                stream=h.stream.name if h.stream else None,
            )
