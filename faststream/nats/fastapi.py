from nats.aio.client import Client as NatsClient
from nats.aio.msg import Msg
from nats.js.client import JetStreamContext
from typing_extensions import Annotated, override

from faststream.broker.fastapi.context import Context, ContextRepo, Logger
from faststream.broker.fastapi.router import StreamRouter
from faststream.nats.broker import NatsBroker as NB
from faststream.nats.message import NatsMessage as NM
from faststream.nats.producer import NatsFastProducer, NatsJSFastProducer

__all__ = (
    "Context",
    "Logger",
    "ContextRepo",
    "NatsRouter",
    "NatsBroker",
    "NatsMessage",
    "Client",
    "JsClient",
    "NatsProducer",
    "NatsJsProducer",
)

NatsMessage = Annotated[NM, Context("message")]
NatsBroker = Annotated[NB, Context("broker")]
Client = Annotated[NatsClient, Context("broker._connection")]
JsClient = Annotated[JetStreamContext, Context("broker._stream")]
NatsProducer = Annotated[NatsFastProducer, Context("broker._producer")]
NatsJsProducer = Annotated[NatsJSFastProducer, Context("broker._js_producer")]


class NatsRouter(StreamRouter[Msg]):
    """A class to represent a NATS router."""

    broker_class = NB

    @override
    @staticmethod
    def _setup_log_context(  # type: ignore[override]
        main_broker: NB,
        including_broker: NB,
    ) -> None:
        for h in including_broker.handlers.values():
            main_broker._setup_log_context(
                queue=h.queue,
                subject=h.subject,
                stream=h.stream.name if h.stream else None,
            )
