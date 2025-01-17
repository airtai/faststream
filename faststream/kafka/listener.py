import logging
from typing import TYPE_CHECKING, Optional

from aiokafka import ConsumerRebalanceListener

from faststream._internal.utils.functions import call_or_await

if TYPE_CHECKING:
    from aiokafka import AIOKafkaConsumer, TopicPartition

    from faststream._internal.basic_types import LoggerProto


def LoggingListenerProxy(  # noqa: N802
    *,
    consumer: "AIOKafkaConsumer",
    logger: Optional["LoggerProto"],
    listener: Optional["ConsumerRebalanceListener"],
) -> Optional["ConsumerRebalanceListener"]:
    if logger is None:
        return listener

    logging_listener = _LoggingListener(consumer=consumer, logger=logger)
    if listener is None:
        return logging_listener

    return _ListenerAggregate(logging_listener, listener)


class _LoggingListener(ConsumerRebalanceListener):
    def __init__(
        self,
        *,
        consumer: "AIOKafkaConsumer",
        logger: "LoggerProto",
    ) -> None:
        self.consumer = consumer
        self.logger = logger

    async def on_partitions_revoked(self, revoked: set["TopicPartition"]) -> None:
        pass

    async def on_partitions_assigned(self, assigned: set["TopicPartition"]) -> None:
        self.logger.log(
            logging.INFO,
            (
                f"Consumer {self.consumer._coordinator.member_id} assigned to partitions: "
                f"{assigned}"
            ),
        )
        if not assigned:
            self.logger.log(
                logging.WARNING,
                (
                    f"Consumer in group {self.consumer._group_id} has no partition assignments - topics "
                    f"{self.consumer._subscription.topics} may have fewer partitions than consumers"
                ),
            )


class _ListenerAggregate(ConsumerRebalanceListener):
    def __init__(
        self,
        *listeners: "ConsumerRebalanceListener",
    ) -> None:
        self.listeners = listeners

    async def on_partitions_revoked(self, revoked: set["TopicPartition"]) -> None:
        for listener in self.listeners:
            await call_or_await(listener.on_partitions_revoked, revoked)

    async def on_partitions_assigned(self, assigned: set["TopicPartition"]) -> None:
        for listener in self.listeners:
            await call_or_await(listener.on_partitions_assigned, assigned)
