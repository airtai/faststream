from nats.aio.client import Client as NatsClient
from nats.js.client import JetStreamContext
from nats.js.object_store import ObjectStore
from typing_extensions import Annotated

from faststream.annotations import ContextRepo, Logger, NoCast
from faststream.nats.broker import NatsBroker as NB
from faststream.nats.message import NatsMessage as NM
from faststream.nats.publisher.producer import NatsFastProducer, NatsJSFastProducer
from faststream.nats.subscriber.usecase import OBJECT_STORAGE_CONTEXT_KEY
from faststream.utils.context import Context

__all__ = (
    "Logger",
    "ContextRepo",
    "NoCast",
    "NatsMessage",
    "NatsBroker",
    "Client",
    "JsClient",
    "ObjectStorage",
)

ObjectStorage = Annotated[ObjectStore, Context(OBJECT_STORAGE_CONTEXT_KEY)]
NatsMessage = Annotated[NM, Context("message")]
NatsBroker = Annotated[NB, Context("broker")]
Client = Annotated[NatsClient, Context("broker._connection")]
JsClient = Annotated[JetStreamContext, Context("broker._stream")]
NatsProducer = Annotated[NatsFastProducer, Context("broker._producer")]
NatsJsProducer = Annotated[NatsJSFastProducer, Context("broker._js_producer")]
