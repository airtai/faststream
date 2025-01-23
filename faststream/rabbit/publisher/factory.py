from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Optional

from faststream._internal.publisher.schemas import (
    PublisherUsecaseOptions,
    SpecificationPublisherOptions,
)
from faststream.rabbit.schemas.base import RabbitBaseOptions
from faststream.rabbit.schemas.publishers import RabbitPublisherBaseOptions

from .specified import SpecificationPublisher

if TYPE_CHECKING:
    from aio_pika import IncomingMessage

    from faststream._internal.types import BrokerMiddleware, PublisherMiddleware
    from faststream.rabbit.schemas import RabbitExchange, RabbitQueue

    from .usecase import PublishKwargs


def create_publisher(
    *,
    routing_key: str,
    queue: "RabbitQueue",
    exchange: "RabbitExchange",
    message_kwargs: "PublishKwargs",
    # Publisher args
    broker_middlewares: Sequence["BrokerMiddleware[IncomingMessage]"],
    middlewares: Sequence["PublisherMiddleware"],
    # AsyncAPI args
    schema_: Optional[Any],
    title_: Optional[str],
    description_: Optional[str],
    include_in_schema: bool,
) -> SpecificationPublisher:
    internal_options = PublisherUsecaseOptions(
        broker_middlewares=broker_middlewares, middlewares=middlewares
    )

    base_options = RabbitPublisherBaseOptions(
        routing_key=routing_key,
        queue=queue,
        exchange=exchange,
        message_kwargs=message_kwargs,
        internal_options=internal_options,
    )

    rabbit_mq_base_options = RabbitBaseOptions(
        queue=queue,
        exchange=exchange,
    )

    specification_options = SpecificationPublisherOptions(
        schema_=schema_,
        title_=title_,
        description_=description_,
        include_in_schema=include_in_schema,
    )

    return SpecificationPublisher(
        base_options=base_options,
        rabbit_mq_base_options=rabbit_mq_base_options,
        specification_options=specification_options,
    )
