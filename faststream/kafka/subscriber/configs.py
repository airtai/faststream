from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Optional,
)

from faststream._internal.subscriber.configs import SubscriberUseCaseConfigs

if TYPE_CHECKING:
    from aiokafka import TopicPartition
    from aiokafka.abc import ConsumerRebalanceListener

    from faststream._internal.basic_types import AnyDict


@dataclass
class KafkaSubscriberBaseConfigs:
    topics: Sequence[str]
    group_id: Optional[str]
    connection_args: "AnyDict"
    listener: Optional["ConsumerRebalanceListener"]
    pattern: Optional[str]
    partitions: Iterable["TopicPartition"]
    internal_configs: SubscriberUseCaseConfigs
