from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Optional,
)

from faststream._internal.subscriber.configs import SubscriberUseCaseConfigs
from faststream.exceptions import SetupError
from faststream.middlewares.acknowledgement.conf import AckPolicy

if TYPE_CHECKING:
    from aiokafka import TopicPartition
    from aiokafka.abc import ConsumerRebalanceListener

    from faststream._internal.basic_types import AnyDict


@dataclass
class KafkaSubscriberBaseConfigs(SubscriberUseCaseConfigs):
    topics: Sequence[str]
    group_id: Optional[str]
    connection_args: "AnyDict"
    listener: Optional["ConsumerRebalanceListener"]
    pattern: Optional[str]
    partitions: Iterable["TopicPartition"]

    def __post_init__(self) -> None:
        if not self.group_id and self.ack_policy is not AckPolicy.ACK_FIRST:
            msg = "You must use `group_id` with manual commit mode."
            raise SetupError(msg)

        if not self.topics and not self.partitions and not self.pattern:
            msg = "You should provide either `topics` or `partitions` or `pattern`."
            raise SetupError(msg)

        if self.topics and self.partitions:
            msg = "You can't provide both `topics` and `partitions`."
            raise SetupError(msg)

        if self.topics and self.pattern:
            msg = "You can't provide both `topics` and `pattern`."
            raise SetupError(msg)

        if self.partitions and self.pattern:
            msg = "You can't provide both `partitions` and `pattern`."
            raise SetupError(msg)
