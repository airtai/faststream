from typing import (
    TYPE_CHECKING,
    Collection,
    Iterable,
    Literal,
    Optional,
    Sequence,
    Tuple,
    Union,
    overload,
)

from faststream.exceptions import SetupError
from faststream.kafka.subscriber.asyncapi import (
    AsyncAPIBatchSubscriber,
    AsyncAPIConcurrentBetweenPartitionsSubscriber,
    AsyncAPIConcurrentDefaultSubscriber,
    AsyncAPIDefaultSubscriber,
)

if TYPE_CHECKING:
    from aiokafka import ConsumerRecord, TopicPartition
    from aiokafka.abc import ConsumerRebalanceListener
    from fast_depends.dependencies import Depends

    from faststream.broker.types import BrokerMiddleware
    from faststream.types import AnyDict


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
    partitions: Collection["TopicPartition"],
    is_manual: bool,
    # Subscriber args
    max_workers: int,
    no_ack: bool,
    no_reply: bool,
    retry: bool,
    broker_dependencies: Iterable["Depends"],
    broker_middlewares: Sequence["BrokerMiddleware[Tuple[ConsumerRecord, ...]]"],
    # AsyncAPI args
    title_: Optional[str],
    description_: Optional[str],
    include_in_schema: bool,
) -> "AsyncAPIBatchSubscriber": ...


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
    partitions: Collection["TopicPartition"],
    is_manual: bool,
    # Subscriber args
    max_workers: int,
    no_ack: bool,
    no_reply: bool,
    retry: bool,
    broker_dependencies: Iterable["Depends"],
    broker_middlewares: Sequence["BrokerMiddleware[ConsumerRecord]"],
    # AsyncAPI args
    title_: Optional[str],
    description_: Optional[str],
    include_in_schema: bool,
) -> Union[
    "AsyncAPIDefaultSubscriber",
    "AsyncAPIConcurrentDefaultSubscriber",
]: ...


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
    partitions: Collection["TopicPartition"],
    is_manual: bool,
    # Subscriber args
    max_workers: int,
    no_ack: bool,
    no_reply: bool,
    retry: bool,
    broker_dependencies: Iterable["Depends"],
    broker_middlewares: Sequence[
        "BrokerMiddleware[Union[ConsumerRecord, Tuple[ConsumerRecord, ...]]]"
    ],
    # AsyncAPI args
    title_: Optional[str],
    description_: Optional[str],
    include_in_schema: bool,
) -> Union[
    "AsyncAPIDefaultSubscriber",
    "AsyncAPIBatchSubscriber",
    "AsyncAPIConcurrentDefaultSubscriber",
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
    partitions: Collection["TopicPartition"],
    is_manual: bool,
    # Subscriber args
    max_workers: int,
    no_ack: bool,
    no_reply: bool,
    retry: bool,
    broker_dependencies: Iterable["Depends"],
    broker_middlewares: Sequence[
        "BrokerMiddleware[Union[ConsumerRecord, Tuple[ConsumerRecord, ...]]]"
    ],
    # AsyncAPI args
    title_: Optional[str],
    description_: Optional[str],
    include_in_schema: bool,
) -> Union[
    "AsyncAPIDefaultSubscriber",
    "AsyncAPIBatchSubscriber",
    "AsyncAPIConcurrentDefaultSubscriber",
    "AsyncAPIConcurrentBetweenPartitionsSubscriber",
]:
    if is_manual and not group_id:
        raise SetupError("You must use `group_id` with manual commit mode.")

    if is_manual and max_workers > 1:
        if len(topics) > 1:
            raise SetupError(
                "You must use a single topic with concurrent manual commit mode."
            )
        if pattern is not None:
            raise SetupError(
                "You can not use a pattern with concurrent manual commit mode."
            )
        if partitions:
            raise SetupError(
                "Manual partition assignment is not supported with concurrent manual commit mode."
            )

    if not topics and not partitions and not pattern:
        raise SetupError(
            "You should provide either `topics` or `partitions` or `pattern`."
        )
    elif topics and partitions:
        raise SetupError("You can't provide both `topics` and `partitions`.")
    elif topics and pattern:
        raise SetupError("You can't provide both `topics` and `pattern`.")
    elif partitions and pattern:
        raise SetupError("You can't provide both `partitions` and `pattern`.")

    if batch:
        return AsyncAPIBatchSubscriber(
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

    else:
        if max_workers > 1:
            if is_manual:
                return AsyncAPIConcurrentBetweenPartitionsSubscriber(
                    topics[0],
                    max_workers=max_workers,
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
            else:
                return AsyncAPIConcurrentDefaultSubscriber(
                    *topics,
                    max_workers=max_workers,
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
        else:
            return AsyncAPIDefaultSubscriber(
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
