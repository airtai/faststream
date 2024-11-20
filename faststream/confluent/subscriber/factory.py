import warnings
from collections.abc import Iterable, Sequence
from typing import (
    TYPE_CHECKING,
    Literal,
    Optional,
    Union,
    overload,
)

from faststream._internal.constants import EMPTY
from faststream.exceptions import SetupError
from faststream.confluent.subscriber.specified import (
    SpecificationBatchSubscriber,
    SpecificationDefaultSubscriber,
)
from faststream.middlewares import AckPolicy

if TYPE_CHECKING:
    from confluent_kafka import Message as ConfluentMsg
    from fast_depends.dependencies import Dependant

    from faststream._internal.basic_types import AnyDict
    from faststream._internal.types import BrokerMiddleware
    from faststream.confluent.schemas import TopicPartition


@overload
def create_subscriber(
    *topics: str,
    partitions: Sequence["TopicPartition"],
    polling_interval: float,
    batch: Literal[True],
    max_records: Optional[int],
    # Kafka information
    group_id: Optional[str],
    connection_data: "AnyDict",
    is_manual: bool,
    # Subscriber args
    ack_policy: "AckPolicy",
    no_reply: bool,
    broker_dependencies: Iterable["Dependant"],
    broker_middlewares: Iterable["BrokerMiddleware[tuple[ConfluentMsg, ...]]"],
    # Specification args
    title_: Optional[str],
    description_: Optional[str],
    include_in_schema: bool,
) -> "SpecificationBatchSubscriber": ...


@overload
def create_subscriber(
    *topics: str,
    partitions: Sequence["TopicPartition"],
    polling_interval: float,
    batch: Literal[False],
    max_records: Optional[int],
    # Kafka information
    group_id: Optional[str],
    connection_data: "AnyDict",
    is_manual: bool,
    # Subscriber args
    ack_policy: "AckPolicy",
    no_reply: bool,
    broker_dependencies: Iterable["Dependant"],
    broker_middlewares: Iterable["BrokerMiddleware[ConfluentMsg]"],
    # Specification args
    title_: Optional[str],
    description_: Optional[str],
    include_in_schema: bool,
) -> "SpecificationDefaultSubscriber": ...


@overload
def create_subscriber(
    *topics: str,
    partitions: Sequence["TopicPartition"],
    polling_interval: float,
    batch: bool,
    max_records: Optional[int],
    # Kafka information
    group_id: Optional[str],
    connection_data: "AnyDict",
    is_manual: bool,
    # Subscriber args
    ack_policy: "AckPolicy",
    no_reply: bool,
    broker_dependencies: Iterable["Dependant"],
    broker_middlewares: Iterable[
        "BrokerMiddleware[Union[ConfluentMsg, tuple[ConfluentMsg, ...]]]"
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
    partitions: Sequence["TopicPartition"],
    polling_interval: float,
    batch: bool,
    max_records: Optional[int],
    # Kafka information
    group_id: Optional[str],
    connection_data: "AnyDict",
    is_manual: bool,
    # Subscriber args
    ack_policy: "AckPolicy",
    no_reply: bool,
    broker_dependencies: Iterable["Dependant"],
    broker_middlewares: Iterable[
        "BrokerMiddleware[Union[ConfluentMsg, tuple[ConfluentMsg, ...]]]"
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
        ack_policy=ack_policy, is_manual=is_manual, group_id=group_id,
    )

    if ack_policy is EMPTY:
        if not is_manual:
            ack_policy = AckPolicy.DO_NOTHING
        else:
            ack_policy = AckPolicy.REJECT_ON_ERROR

    if batch:
        return SpecificationBatchSubscriber(
            *topics,
            partitions=partitions,
            polling_interval=polling_interval,
            max_records=max_records,
            group_id=group_id,
            connection_data=connection_data,
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
        partitions=partitions,
        polling_interval=polling_interval,
        group_id=group_id,
        connection_data=connection_data,
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
    *,
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

