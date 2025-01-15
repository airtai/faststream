from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from aio_pika import IncomingMessage

    from faststream._internal.types import BrokerMiddleware, PublisherMiddleware
    from faststream.rabbit.publisher.usecase import PublishKwargs
    from faststream.rabbit.schemas.exchange import RabbitExchange
    from faststream.rabbit.schemas.queue import RabbitQueue


@dataclass
class LogicOptions:
    routing_key: str
    queue: "RabbitQueue"
    exchange: "RabbitExchange"
    # PublishCommand options
    message_kwargs: "PublishKwargs"
    # Publisher args
    broker_middlewares: Sequence["BrokerMiddleware[IncomingMessage]"]
    middlewares: Sequence["PublisherMiddleware"]


@dataclass
class SpecificationOptions:
    schema_: Optional[Any]
    title_: Optional[str]
    description_: Optional[str]
    include_in_schema: bool
