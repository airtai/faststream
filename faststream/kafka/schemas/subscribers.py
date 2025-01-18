from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Optional,
)

from faststream._internal.subscriber.schemas import SubscriberUsecaseOptions

if TYPE_CHECKING:
    from aiokafka import TopicPartition
    from aiokafka.abc import ConsumerRebalanceListener

    from faststream._internal.basic_types import AnyDict


@dataclass
class SubscriberDefaultOptions:
    topics: Sequence[str]
    group_id: Optional[str]
    connection_args: "AnyDict"
    listener: Optional["ConsumerRebalanceListener"]
    pattern: Optional[str]
    partitions: Iterable["TopicPartition"]


@dataclass
class SubscriberLogicOptions(SubscriberDefaultOptions):
    internal_options: SubscriberUsecaseOptions
