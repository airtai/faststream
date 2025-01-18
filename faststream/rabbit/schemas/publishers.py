from dataclasses import dataclass
from typing import TYPE_CHECKING

from faststream._internal.publisher.schemas import (
    PublisherUsecaseOptions,
)

if TYPE_CHECKING:
    from faststream.rabbit.publisher.usecase import PublishKwargs
    from faststream.rabbit.schemas.exchange import RabbitExchange
    from faststream.rabbit.schemas.queue import RabbitQueue


@dataclass
class RabbitLogicPublisherOptions:
    routing_key: str
    queue: "RabbitQueue"
    exchange: "RabbitExchange"
    # PublishCommand options
    message_kwargs: "PublishKwargs"
    # Publisher args
    internal_options: PublisherUsecaseOptions
