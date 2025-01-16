from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Optional,
)

if TYPE_CHECKING:
    from confluent_kafka import Message
    from fast_depends.dependencies import Dependant

    from faststream._internal.basic_types import AnyDict
    from faststream._internal.types import (
        AsyncCallable,
        BrokerMiddleware,
    )
    from faststream.confluent.schemas import TopicPartition
    from faststream.middlewares import AckPolicy


@dataclass
class DefaultOptions:
    topics: Sequence[str]
    partitions: Sequence["TopicPartition"]
    polling_interval: float
    group_id: Optional[str]
    connection_data: "AnyDict"
    ack_policy: "AckPolicy"
    no_reply: bool
    broker_dependencies: Iterable["Dependant"]
    broker_middlewares: Sequence["BrokerMiddleware[Message]"]


@dataclass
class LogicOptions(DefaultOptions):
    default_parser: "AsyncCallable"
    default_decoder: "AsyncCallable"


@dataclass
class SpecificationOptions:
    topics: Sequence[str]
    partitions: Sequence["TopicPartition"]
    polling_interval: float
    group_id: Optional[str]
    connection_data: "AnyDict"
    ack_policy: "AckPolicy"
    no_reply: bool
    broker_dependencies: Iterable["Dependant"]
    broker_middlewares: Sequence["BrokerMiddleware[Message]"]
    title_: Optional[str]
    description_: Optional[str]
    include_in_schema: bool
