from typing import (
    TYPE_CHECKING,
    Iterable,
    Literal,
    Optional,
    Sequence,
    Tuple,
    Union,
    overload,
)

from faststream.confluent.subscriber.asyncapi import (
    AsyncAPIBatchSubscriber,
    AsyncAPIDefaultSubscriber,
)

if TYPE_CHECKING:
    from confluent_kafka import Message as ConfluentMsg
    from fast_depends.dependencies import Depends

    from faststream.broker.types import BrokerMiddleware
    from faststream.confluent.schemas import TopicPartition
    from faststream.types import AnyDict


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
    no_ack: bool,
    no_reply: bool,
    retry: bool,
    broker_dependencies: Iterable["Depends"],
    broker_middlewares: Iterable["BrokerMiddleware[Tuple[ConfluentMsg, ...]]"],
    # AsyncAPI args
    title_: Optional[str],
    description_: Optional[str],
    include_in_schema: bool,
) -> "AsyncAPIBatchSubscriber": ...


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
    no_ack: bool,
    no_reply: bool,
    retry: bool,
    broker_dependencies: Iterable["Depends"],
    broker_middlewares: Iterable["BrokerMiddleware[ConfluentMsg]"],
    # AsyncAPI args
    title_: Optional[str],
    description_: Optional[str],
    include_in_schema: bool,
) -> "AsyncAPIDefaultSubscriber": ...


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
    no_ack: bool,
    no_reply: bool,
    retry: bool,
    broker_dependencies: Iterable["Depends"],
    broker_middlewares: Iterable[
        "BrokerMiddleware[Union[ConfluentMsg, Tuple[ConfluentMsg, ...]]]"
    ],
    # AsyncAPI args
    title_: Optional[str],
    description_: Optional[str],
    include_in_schema: bool,
) -> Union[
    "AsyncAPIDefaultSubscriber",
    "AsyncAPIBatchSubscriber",
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
    no_ack: bool,
    no_reply: bool,
    retry: bool,
    broker_dependencies: Iterable["Depends"],
    broker_middlewares: Iterable[
        "BrokerMiddleware[Union[ConfluentMsg, Tuple[ConfluentMsg, ...]]]"
    ],
    # AsyncAPI args
    title_: Optional[str],
    description_: Optional[str],
    include_in_schema: bool,
) -> Union[
    "AsyncAPIDefaultSubscriber",
    "AsyncAPIBatchSubscriber",
]:
    if batch:
        return AsyncAPIBatchSubscriber(
            *topics,
            partitions=partitions,
            polling_interval=polling_interval,
            max_records=max_records,
            group_id=group_id,
            connection_data=connection_data,
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
            partitions=partitions,
            polling_interval=polling_interval,
            group_id=group_id,
            connection_data=connection_data,
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
