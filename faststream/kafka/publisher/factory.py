from collections.abc import Iterable
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    Optional,
    Union,
    overload,
)

from faststream.exceptions import SetupError

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
    broker_middlewares: Iterable["BrokerMiddleware[tuple[ConsumerRecord, ...]]"],
    middlewares: Iterable["PublisherMiddleware"],
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
    broker_middlewares: Iterable["BrokerMiddleware[ConsumerRecord]"],
    middlewares: Iterable["PublisherMiddleware"],
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
    broker_middlewares: Iterable[
        "BrokerMiddleware[Union[tuple[ConsumerRecord, ...], ConsumerRecord]]"
    ],
    middlewares: Iterable["PublisherMiddleware"],
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
    broker_middlewares: Iterable[
        "BrokerMiddleware[Union[tuple[ConsumerRecord, ...], ConsumerRecord]]"
    ],
    middlewares: Iterable["PublisherMiddleware"],
    # Specification args
    schema_: Optional[Any],
    title_: Optional[str],
    description_: Optional[str],
    include_in_schema: bool,
) -> Union[
    "SpecificationBatchPublisher",
    "SpecificationDefaultPublisher",
]:
    if batch:
        if key:
            msg = "You can't setup `key` with batch publisher"
            raise SetupError(msg)

        return SpecificationBatchPublisher(
            topic=topic,
            partition=partition,
            headers=headers,
            reply_to=reply_to,
            broker_middlewares=broker_middlewares,
            middlewares=middlewares,
            schema_=schema_,
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )
    return SpecificationDefaultPublisher(
        key=key,
        # basic args
        topic=topic,
        partition=partition,
        headers=headers,
        reply_to=reply_to,
        broker_middlewares=broker_middlewares,
        middlewares=middlewares,
        schema_=schema_,
        title_=title_,
        description_=description_,
        include_in_schema=include_in_schema,
    )
