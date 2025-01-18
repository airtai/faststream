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
from faststream._internal.subscriber.schemas import SubscriberUsecaseOptions
from faststream.confluent.schemas.subscribers import SubscriberLogicOptions
from faststream.confluent.subscriber.specified import (
    SpecificationBatchSubscriber,
    SpecificationConcurrentDefaultSubscriber,
    SpecificationDefaultSubscriber,
)
from faststream.exceptions import SetupError
from faststream.middlewares import AckPolicy
from faststream.specification.schema.base import SpecificationOptions

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
    auto_commit: bool,
    # Subscriber args
    ack_policy: "AckPolicy",
    no_ack: bool,
    max_workers: int,
    no_reply: bool,
    broker_dependencies: Iterable["Dependant"],
    broker_middlewares: Sequence["BrokerMiddleware[tuple[ConfluentMsg, ...]]"],
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
    auto_commit: bool,
    # Subscriber args
    ack_policy: "AckPolicy",
    no_ack: bool,
    max_workers: int,
    no_reply: bool,
    broker_dependencies: Iterable["Dependant"],
    broker_middlewares: Sequence["BrokerMiddleware[ConfluentMsg]"],
    # Specification args
    title_: Optional[str],
    description_: Optional[str],
    include_in_schema: bool,
) -> Union[
    "SpecificationDefaultSubscriber",
    "SpecificationConcurrentDefaultSubscriber",
]: ...


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
    auto_commit: bool,
    # Subscriber args
    ack_policy: "AckPolicy",
    no_ack: bool,
    max_workers: int,
    no_reply: bool,
    broker_dependencies: Iterable["Dependant"],
    broker_middlewares: Union[
        Sequence["BrokerMiddleware[tuple[ConfluentMsg, ...]]"],
        Sequence["BrokerMiddleware[ConfluentMsg]"],
    ],
    # Specification args
    title_: Optional[str],
    description_: Optional[str],
    include_in_schema: bool,
) -> Union[
    "SpecificationDefaultSubscriber",
    "SpecificationBatchSubscriber",
    "SpecificationConcurrentDefaultSubscriber",
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
    auto_commit: bool,
    # Subscriber args
    ack_policy: "AckPolicy",
    no_ack: bool,
    max_workers: int,
    no_reply: bool,
    broker_dependencies: Iterable["Dependant"],
    broker_middlewares: Union[
        Sequence["BrokerMiddleware[tuple[ConfluentMsg, ...]]"],
        Sequence["BrokerMiddleware[ConfluentMsg]"],
    ],
    # Specification args
    title_: Optional[str],
    description_: Optional[str],
    include_in_schema: bool,
) -> Union[
    "SpecificationDefaultSubscriber",
    "SpecificationBatchSubscriber",
    "SpecificationConcurrentDefaultSubscriber",
]:
    _validate_input_for_misconfigure(
        *topics,
        partitions=partitions,
        ack_policy=ack_policy,
        no_ack=no_ack,
        auto_commit=auto_commit,
        group_id=group_id,
        max_workers=max_workers,
    )

    if auto_commit is not EMPTY:
        ack_policy = AckPolicy.ACK_FIRST if auto_commit else AckPolicy.REJECT_ON_ERROR

    if no_ack is not EMPTY:
        ack_policy = AckPolicy.DO_NOTHING if no_ack else EMPTY

    if ack_policy is EMPTY:
        ack_policy = AckPolicy.ACK_FIRST

    if ack_policy is AckPolicy.ACK_FIRST:
        connection_data["enable_auto_commit"] = True
        ack_policy = AckPolicy.DO_NOTHING

    internal_options = SubscriberUsecaseOptions(
        ack_policy=ack_policy,
        no_reply=no_reply,
        broker_dependencies=broker_dependencies,
        broker_middlewares=broker_middlewares,
        default_decoder=EMPTY,
        default_parser=EMPTY,
    )

    options = SubscriberLogicOptions(
        topics=topics,
        partitions=partitions,
        polling_interval=polling_interval,
        group_id=group_id,
        connection_data=connection_data,
        internal_options=internal_options,
    )

    specification_options = SpecificationOptions(
        title_=title_,
        description_=description_,
        include_in_schema=include_in_schema,
    )

    if batch:
        return SpecificationBatchSubscriber(
            specification_options=specification_options,
            options=options,
            max_records=max_records,
        )

    if max_workers > 1:
        return SpecificationConcurrentDefaultSubscriber(
            specification_options=specification_options,
            options=options,
            # concurrent arg
            max_workers=max_workers,
        )

    return SpecificationDefaultSubscriber(
        specification_options=specification_options,
        options=options,
    )


def _validate_input_for_misconfigure(
    *topics: str,
    partitions: Sequence["TopicPartition"],
    ack_policy: "AckPolicy",
    auto_commit: bool,
    no_ack: bool,
    group_id: Optional[str],
    max_workers: int,
) -> None:
    if auto_commit is not EMPTY:
        warnings.warn(
            "`auto_commit` option was deprecated in prior to `ack_policy=AckPolicy.ACK_FIRST`. Scheduled to remove in 0.7.0",
            category=DeprecationWarning,
            stacklevel=4,
        )

        if ack_policy is not EMPTY:
            msg = "You can't use deprecated `auto_commit` and `ack_policy` simultaneously. Please, use `ack_policy` only."
            raise SetupError(msg)

        ack_policy = AckPolicy.ACK_FIRST if auto_commit else AckPolicy.REJECT_ON_ERROR

    if no_ack is not EMPTY:
        warnings.warn(
            "`no_ack` option was deprecated in prior to `ack_policy=AckPolicy.DO_NOTHING`. Scheduled to remove in 0.7.0",
            category=DeprecationWarning,
            stacklevel=4,
        )

        if ack_policy is not EMPTY:
            msg = "You can't use deprecated `no_ack` and `ack_policy` simultaneously. Please, use `ack_policy` only."
            raise SetupError(msg)

        ack_policy = AckPolicy.DO_NOTHING if no_ack else EMPTY

    if ack_policy is EMPTY:
        ack_policy = AckPolicy.ACK_FIRST

    if AckPolicy.ACK_FIRST is not AckPolicy.ACK_FIRST and max_workers > 1:
        msg = "Max workers not work with manual commit mode."
        raise SetupError(msg)

    if not group_id and ack_policy is not AckPolicy.ACK_FIRST:
        msg = "You must use `group_id` with manual commit mode."
        raise SetupError(msg)

    if not topics and not partitions:
        msg = "You should provide either `topics` or `partitions`."
        raise SetupError(msg)
    if topics and partitions:
        msg = "You can't provide both `topics` and `partitions`."
        raise SetupError(msg)
