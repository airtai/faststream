from typing import (
    TYPE_CHECKING,
    Callable,
    Iterable,
    Literal,
    Optional,
    Tuple,
    Union,
    overload,
)

from faststream.kafka.subscriber.asyncapi import (
    AsyncAPIBatchSubscriber,
    AsyncAPIDefaultSubscriber,
)

if TYPE_CHECKING:
    from aiokafka import AIOKafkaConsumer, ConsumerRecord
    from aiokafka.abc import ConsumerRebalanceListener
    from fast_depends.dependencies import Depends

    from faststream.broker.types import BrokerMiddleware


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
    builder: Callable[..., "AIOKafkaConsumer"],
    is_manual: bool,
    # Subscriber args
    no_ack: bool,
    retry: bool,
    broker_dependencies: Iterable["Depends"],
    broker_middlewares: Iterable["BrokerMiddleware[Tuple[ConsumerRecord, ...]]"],
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
    builder: Callable[..., "AIOKafkaConsumer"],
    is_manual: bool,
    # Subscriber args
    no_ack: bool,
    retry: bool,
    broker_dependencies: Iterable["Depends"],
    broker_middlewares: Iterable["BrokerMiddleware[ConsumerRecord]"],
    # AsyncAPI args
    title_: Optional[str],
    description_: Optional[str],
    include_in_schema: bool,
) -> "AsyncAPIDefaultSubscriber": ...


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
    builder: Callable[..., "AIOKafkaConsumer"],
    is_manual: bool,
    # Subscriber args
    no_ack: bool,
    retry: bool,
    broker_dependencies: Iterable["Depends"],
    broker_middlewares: Iterable[
        "BrokerMiddleware[Union[ConsumerRecord, Tuple[ConsumerRecord, ...]]]"
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
    batch: bool,
    batch_timeout_ms: int,
    max_records: Optional[int],
    # Kafka information
    group_id: Optional[str],
    listener: Optional["ConsumerRebalanceListener"],
    pattern: Optional[str],
    builder: Callable[..., "AIOKafkaConsumer"],
    is_manual: bool,
    # Subscriber args
    no_ack: bool,
    retry: bool,
    broker_dependencies: Iterable["Depends"],
    broker_middlewares: Iterable[
        "BrokerMiddleware[Union[ConsumerRecord, Tuple[ConsumerRecord, ...]]]"
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
            batch_timeout_ms=batch_timeout_ms,
            max_records=max_records,
            group_id=group_id,
            listener=listener,
            pattern=pattern,
            builder=builder,
            is_manual=is_manual,
            no_ack=no_ack,
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
            builder=builder,
            is_manual=is_manual,
            no_ack=no_ack,
            retry=retry,
            broker_dependencies=broker_dependencies,
            broker_middlewares=broker_middlewares,
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )
