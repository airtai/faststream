from collections.abc import Sequence
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    Optional,
    Union,
    overload,
)

from faststream._internal.publisher.schemas import (
    PublisherUsecaseOptions,
)
from faststream.exceptions import SetupError
from faststream.kafka.schemas.publishers import KafkaPublisherBaseOptions
from faststream.specification.schema.base import SpecificationOptions

from .specified import SpecificationBatchPublisher, SpecificationDefaultPublisher

if TYPE_CHECKING:
    from aiokafka import ConsumerRecord

    from faststream._internal.types import BrokerMiddleware, PublisherMiddleware


@overload
def create_publisher(
    *,
    batch: Literal[True],
    key: Optional[bytes],
    topic: str,
    partition: Optional[int],
    headers: Optional[dict[str, str]],
    reply_to: str,
    # Publisher args
    broker_middlewares: Sequence["BrokerMiddleware[tuple[ConsumerRecord, ...]]"],
    middlewares: Sequence["PublisherMiddleware"],
    # Specification args
    schema_: Optional[Any],
    title_: Optional[str],
    description_: Optional[str],
    include_in_schema: bool,
) -> "SpecificationBatchPublisher": ...


@overload
def create_publisher(
    *,
    batch: Literal[False],
    key: Optional[bytes],
    topic: str,
    partition: Optional[int],
    headers: Optional[dict[str, str]],
    reply_to: str,
    # Publisher args
    broker_middlewares: Sequence["BrokerMiddleware[ConsumerRecord]"],
    middlewares: Sequence["PublisherMiddleware"],
    # Specification args
    schema_: Optional[Any],
    title_: Optional[str],
    description_: Optional[str],
    include_in_schema: bool,
) -> "SpecificationDefaultPublisher": ...


@overload
def create_publisher(
    *,
    batch: bool,
    key: Optional[bytes],
    topic: str,
    partition: Optional[int],
    headers: Optional[dict[str, str]],
    reply_to: str,
    # Publisher args
    broker_middlewares: Sequence[
        "BrokerMiddleware[Union[tuple[ConsumerRecord, ...], ConsumerRecord]]"
    ],
    middlewares: Sequence["PublisherMiddleware"],
    # Specification args
    schema_: Optional[Any],
    title_: Optional[str],
    description_: Optional[str],
    include_in_schema: bool,
) -> Union[
    "SpecificationBatchPublisher",
    "SpecificationDefaultPublisher",
]: ...


def create_publisher(
    *,
    batch: bool,
    key: Optional[bytes],
    topic: str,
    partition: Optional[int],
    headers: Optional[dict[str, str]],
    reply_to: str,
    # Publisher args
    broker_middlewares: Sequence[
        "BrokerMiddleware[Union[tuple[ConsumerRecord, ...], ConsumerRecord]]"
    ],
    middlewares: Sequence["PublisherMiddleware"],
    # Specification args
    schema_: Optional[Any],
    title_: Optional[str],
    description_: Optional[str],
    include_in_schema: bool,
) -> Union[
    "SpecificationBatchPublisher",
    "SpecificationDefaultPublisher",
]:
    internal_options = PublisherUsecaseOptions(
        broker_middlewares=broker_middlewares, middlewares=middlewares
    )
    base_options = KafkaPublisherBaseOptions(
        key=key,
        topic=topic,
        partition=partition,
        headers=headers,
        reply_to=reply_to,
        internal_options=internal_options,
    )
    specification_options = SpecificationOptions(
        title_=title_,
        description_=description_,
        include_in_schema=include_in_schema,
    )

    if batch:
        if key:
            msg = "You can't setup `key` with batch publisher"
            raise SetupError(msg)

        return SpecificationBatchPublisher(
            base_options=base_options,
            specification_options=specification_options,
            schema_=schema_,
        )
    return SpecificationDefaultPublisher(
        base_options=base_options,
        specification_options=specification_options,
        schema_=schema_,
    )
