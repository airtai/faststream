import warnings
from collections.abc import Iterable
from typing import (
    TYPE_CHECKING,
    Literal,
    Optional,
    Union,
    overload,
)

from faststream._internal.constants import EMPTY
from faststream.exceptions import SetupError
from faststream.kafka.subscriber.specified import (
    SpecificationBatchSubscriber,
    SpecificationDefaultSubscriber,
)
from faststream.middlewares import AckPolicy

if TYPE_CHECKING:
    from aiokafka import ConsumerRecord, TopicPartition
    from aiokafka.abc import ConsumerRebalanceListener
    from fast_depends.dependencies import Dependant

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
    ack_policy: "AckPolicy",
    no_reply: bool,
    broker_dependencies: Iterable["Dependant"],
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
    ack_policy: "AckPolicy",
    no_reply: bool,
    broker_dependencies: Iterable["Dependant"],
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
    ack_policy: "AckPolicy",
    no_reply: bool,
    broker_dependencies: Iterable["Dependant"],
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
    ack_policy: "AckPolicy",
    no_reply: bool,
    broker_dependencies: Iterable["Dependant"],
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
    _validate_input_for_misconfigure(
        *topics,
        pattern=pattern,
        partitions=partitions,
        ack_policy=ack_policy,
        is_manual=is_manual,
        group_id=group_id,
    )

    if ack_policy is EMPTY:
        if not is_manual:
            ack_policy = AckPolicy.DO_NOTHING
        else:
            ack_policy = AckPolicy.REJECT_ON_ERROR

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
            ack_policy=ack_policy,
            no_reply=no_reply,
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
        ack_policy=ack_policy,
        no_reply=no_reply,
        broker_dependencies=broker_dependencies,
        broker_middlewares=broker_middlewares,
        title_=title_,
        description_=description_,
        include_in_schema=include_in_schema,
    )


def _validate_input_for_misconfigure(
    *topics: str,
    partitions: Iterable["TopicPartition"],
    pattern: Optional[str],
    ack_policy: "AckPolicy",
    is_manual: bool,
    group_id: Optional[str],
) -> None:
    if not is_manual and ack_policy is not EMPTY and ack_policy is not AckPolicy.ACK_FIRST:
        warnings.warn(
            "You can't use ack_policy other then AckPolicy.ACK_FIRST with `auto_commit=True`",
            RuntimeWarning,
            stacklevel=4,
        )
    elif is_manual and ack_policy is not EMPTY and ack_policy is AckPolicy.ACK_FIRST:
        warnings.warn(
            "You can't use AckPolicy.ACK_FIRST with `auto_commit=False`",
            RuntimeWarning,
            stacklevel=4,
        )

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
