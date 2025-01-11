import logging
from typing import TYPE_CHECKING, Optional, Set

from aiokafka import ConsumerRebalanceListener

if TYPE_CHECKING:
    from aiokafka import AIOKafkaConsumer, TopicPartition

    from faststream.types import LoggerProto


class DefaultLoggingConsumerRebalanceListener(ConsumerRebalanceListener):  # type: ignore[misc]
    def __init__(
        self,
        consumer: "AIOKafkaConsumer",
        logger: Optional["LoggerProto"],
    ):
        self.consumer = consumer
        self.logger = logger

    def on_partitions_revoked(self, revoked: Set["TopicPartition"]) -> None:
        pass

    def on_partitions_assigned(self, assigned: Set["TopicPartition"]) -> None:
        if self.logger:
            self.logger.log(
                logging.INFO,
                "Consumer %s assigned to partitions: %s",
                self.consumer._coordinator.member_id,
                assigned,
            )
            if not assigned:
                self.logger.log(
                    logging.WARNING,
                    "Consumer in group %s has no partition assignments - topics "
                    "%s may have fewer partitions than consumers",
                    self.consumer._group_id,
                    self.consumer._subscription.topics,
                )
