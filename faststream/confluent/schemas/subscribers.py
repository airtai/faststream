from collections.abc import Sequence
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Optional,
)

from faststream._internal.subscriber.schemas import SubscriberUsecaseOptions

if TYPE_CHECKING:
    from faststream._internal.basic_types import AnyDict
    from faststream.confluent.schemas import TopicPartition


@dataclass
class SubscriberDefaultOptions:
    topics: Sequence[str]
    partitions: Sequence["TopicPartition"]
    polling_interval: float
    group_id: Optional[str]
    connection_data: "AnyDict"


@dataclass
class SubscriberLogicOptions(SubscriberDefaultOptions):
    internal_options: SubscriberUsecaseOptions
