import logging
from typing import TYPE_CHECKING, Optional

from aiokafka import ConsumerRebalanceListener

from faststream._internal.utils.functions import call_or_await

if TYPE_CHECKING:
    from aiokafka import AIOKafkaConsumer, TopicPartition

    from faststream._internal.basic_types import AnyDict, LoggerProto


def make_logging_listener(
    *,
    consumer: "AIOKafkaConsumer",
    logger: Optional["LoggerProto"],
    log_extra: "AnyDict",
    listener: Optional["ConsumerRebalanceListener"],
) -> Optional["ConsumerRebalanceListener"]:
    if logger is None:
        return listener

    logging_listener = _LoggingListener(
        consumer=consumer,
        logger=logger,
        log_extra=log_extra,
    )
    if listener is None:
        return logging_listener

    return _LoggingListenerFacade(
        logging_listener=logging_listener,
        listener=listener,
    )


class _LoggingListener(ConsumerRebalanceListener):
    def __init__(
        self,
        *,
        consumer: "AIOKafkaConsumer",
        logger: "LoggerProto",
        log_extra: "AnyDict",
    ) -> None:
        self.consumer = consumer
        self.logger = logger
        self.log_extra = log_extra

    async def on_partitions_revoked(self, revoked: set["TopicPartition"]) -> None:
        pass

    async def on_partitions_assigned(self, assigned: set["TopicPartition"]) -> None:
        self.logger.log(
            logging.INFO,
            (
                f"Consumer {self.consumer._coordinator.member_id} assigned to partitions: "
                f"{assigned}"
            ),
            extra=self.log_extra,
        )
        if not assigned:
            self.logger.log(
                logging.WARNING,
                (
                    f"Consumer in group {self.consumer._group_id} has no partition assignments - topics "
                    f"{self.consumer._subscription.topics} may have fewer partitions than consumers"
                ),
                extra=self.log_extra,
            )


class _LoggingListenerFacade(ConsumerRebalanceListener):
    def __init__(
        self,
        *,
        logging_listener: _LoggingListener,
        listener: ConsumerRebalanceListener,
    ) -> None:
        self.logging_listener = logging_listener
        self.listener = listener

    async def on_partitions_revoked(self, revoked: set["TopicPartition"]) -> None:
        await call_or_await(self.listener.on_partitions_revoked, revoked)

    async def on_partitions_assigned(self, assigned: set["TopicPartition"]) -> None:
        await self.logging_listener.on_partitions_revoked(assigned)
        await call_or_await(self.listener.on_partitions_assigned, assigned)
