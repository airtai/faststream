from collections.abc import Iterable
from typing import (
    TYPE_CHECKING,
    Literal,
    Optional,
    Union,
    overload,
)

from faststream.exceptions import SetupError
from faststream.kafka.subscriber.specified import (
    SpecificationBatchSubscriber,
    SpecificationDefaultSubscriber,
)

if TYPE_CHECKING:
    from aiokafka import ConsumerRecord, TopicPartition
    from aiokafka.abc import ConsumerRebalanceListener
    from fast_depends.dependencies import Depends

    from faststream._internal.basic_types import AnyDict
    from faststream._internal.types import BrokerMiddleware


@overload
def create_subscriber(
    *topics: str,
    batch: Literal[True],
    batch_timeout_ms: int,
    max_records: Optional[int],
    # Kafka information
    group_id: Optional[str],
    listener: Optional["ConsumerRebalanceListener"],
    pattern: Optional[str],
    connection_args: "AnyDict",
    partitions: Iterable["TopicPartition"],
    is_manual: bool,
    # Subscriber args
    no_ack: bool,
    no_reply: bool,
    retry: bool,
    broker_dependencies: Iterable["Depends"],
    broker_middlewares: Iterable["BrokerMiddleware[tuple[ConsumerRecord, ...]]"],
    # Specification args
    title_: Optional[str],
    description_: Optional[str],
    include_in_schema: bool,
) -> "SpecificationBatchSubscriber": ...


@overload
def create_subscriber(
    *topics: str,
    batch: Literal[False],
    batch_timeout_ms: int,
    max_records: Optional[int],
    # Kafka information
    group_id: Optional[str],
    listener: Optional["ConsumerRebalanceListener"],
    pattern: Optional[str],
    connection_args: "AnyDict",
    partitions: Iterable["TopicPartition"],
    is_manual: bool,
    # Subscriber args
    no_ack: bool,
    no_reply: bool,
    retry: bool,
    broker_dependencies: Iterable["Depends"],
    broker_middlewares: Iterable["BrokerMiddleware[ConsumerRecord]"],
    # Specification args
    title_: Optional[str],
    description_: Optional[str],
    include_in_schema: bool,
) -> "SpecificationDefaultSubscriber": ...


@overload
def create_subscriber(
    *topics: str,
    batch: bool,
    batch_timeout_ms: int,
    max_records: Optional[int],
    # Kafka information
    group_id: Optional[str],
    listener: Optional["ConsumerRebalanceListener"],
    pattern: Optional[str],
    connection_args: "AnyDict",
    partitions: Iterable["TopicPartition"],
    is_manual: bool,
    # Subscriber args
    no_ack: bool,
    no_reply: bool,
    retry: bool,
    broker_dependencies: Iterable["Depends"],
    broker_middlewares: Iterable[
        "BrokerMiddleware[Union[ConsumerRecord, tuple[ConsumerRecord, ...]]]"
    ],
    # Specification args
    title_: Optional[str],
    description_: Optional[str],
    include_in_schema: bool,
) -> Union[
    "SpecificationDefaultSubscriber",
    "SpecificationBatchSubscriber",
]: ...


def create_subscriber(
    *topics: str,
    batch: bool,
    batch_timeout_ms: int,
    max_records: Optional[int],
    # Kafka information
    group_id: Optional[str],
    listener: Optional["ConsumerRebalanceListener"],
    pattern: Optional[str],
    connection_args: "AnyDict",
    partitions: Iterable["TopicPartition"],
    is_manual: bool,
    # Subscriber args
    no_ack: bool,
    no_reply: bool,
    retry: bool,
    broker_dependencies: Iterable["Depends"],
    broker_middlewares: Iterable[
        "BrokerMiddleware[Union[ConsumerRecord, tuple[ConsumerRecord, ...]]]"
    ],
    # Specification args
    title_: Optional[str],
    description_: Optional[str],
    include_in_schema: bool,
) -> Union[
    "SpecificationDefaultSubscriber",
    "SpecificationBatchSubscriber",
]:
    if is_manual and not group_id:
        msg = "You must use `group_id` with manual commit mode."
        raise SetupError(msg)

    if not topics and not partitions and not pattern:
        msg = "You should provide either `topics` or `partitions` or `pattern`."
        raise SetupError(
            msg,
        )
    if topics and partitions:
        msg = "You can't provide both `topics` and `partitions`."
        raise SetupError(msg)
    if topics and pattern:
        msg = "You can't provide both `topics` and `pattern`."
        raise SetupError(msg)
    if partitions and pattern:
        msg = "You can't provide both `partitions` and `pattern`."
        raise SetupError(msg)

    if batch:
        return SpecificationBatchSubscriber(
            *topics,
            batch_timeout_ms=batch_timeout_ms,
            max_records=max_records,
            group_id=group_id,
            listener=listener,
            pattern=pattern,
            connection_args=connection_args,
            partitions=partitions,
            is_manual=is_manual,
            no_ack=no_ack,
            no_reply=no_reply,
            retry=retry,
            broker_dependencies=broker_dependencies,
            broker_middlewares=broker_middlewares,
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

    return SpecificationDefaultSubscriber(
        *topics,
        group_id=group_id,
        listener=listener,
        pattern=pattern,
        connection_args=connection_args,
        partitions=partitions,
        is_manual=is_manual,
        no_ack=no_ack,
        no_reply=no_reply,
        retry=retry,
        broker_dependencies=broker_dependencies,
        broker_middlewares=broker_middlewares,
        title_=title_,
        description_=description_,
        include_in_schema=include_in_schema,
    )
