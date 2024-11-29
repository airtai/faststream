from nats.aio.client import Client as NatsClient
from nats.js.client import JetStreamContext
from typing_extensions import Annotated

from faststream.broker.fastapi.context import Context, ContextRepo, Logger
from faststream.nats.broker import NatsBroker as NB
from faststream.nats.fastapi.fastapi import NatsRouter
from faststream.nats.message import NatsMessage as NM
from faststream.nats.publisher.producer import NatsFastProducer, NatsJSFastProducer

NatsMessage = Annotated[NM, Context("message")]
NatsBroker = Annotated[NB, Context("broker")]
Client = Annotated[NatsClient, Context("broker._connection")]
JsClient = Annotated[JetStreamContext, Context("broker._stream")]
NatsProducer = Annotated[NatsFastProducer, Context("broker._producer")]
NatsJsProducer = Annotated[NatsJSFastProducer, Context("broker._js_producer")]

__all__ = (
    "Client",
    "Context",
    "ContextRepo",
    "JsClient",
    "Logger",
    "NatsBroker",
    "NatsJsProducer",
    "NatsMessage",
    "NatsProducer",
    "NatsRouter",
)
