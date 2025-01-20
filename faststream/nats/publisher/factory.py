from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, Any, Optional

from faststream._internal.publisher.schemas import (
    PublisherUsecaseOptions,
)
from faststream.nats.schemas.publishers import NatsPublisherBaseOptions
from faststream.specification.schema.base import SpecificationOptions

from .specified import SpecificationPublisher

if TYPE_CHECKING:
    from nats.aio.msg import Msg

    from faststream._internal.types import BrokerMiddleware, PublisherMiddleware
    from faststream.nats.schemas.js_stream import JStream


def create_publisher(
    *,
    subject: str,
    reply_to: str,
    headers: Optional[dict[str, str]],
    stream: Optional["JStream"],
    timeout: Optional[float],
    # Publisher args
    broker_middlewares: Iterable["BrokerMiddleware[Msg]"],
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

    base_options = NatsPublisherBaseOptions(
        subject=subject,
        stream=stream,
        reply_to=reply_to,
        headers=headers,
        timeout=timeout,
        internal_options=internal_options,
    )

    specification_options = SpecificationOptions(
        title_=title_,
        description_=description_,
        include_in_schema=include_in_schema,
    )

    return SpecificationPublisher(
        base_options=base_options,
        specification_options=specification_options,
        schema_=schema_
    )
