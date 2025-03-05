import asyncio
import logging
from typing import TYPE_CHECKING, Optional, Set

from aiokafka import ConsumerRebalanceListener

if TYPE_CHECKING:
    from aiokafka import AIOKafkaConsumer, TopicPartition

    from faststream.types import AnyDict, LoggerProto


class LoggingListenerProxy(ConsumerRebalanceListener):  # type: ignore[misc]
    """Logs partition assignments and passes calls to user-supplied listener."""

    _log_unassigned_consumer_delay_seconds = 60 * 2

    def __init__(
        self,
        consumer: "AIOKafkaConsumer",
        logger: Optional["LoggerProto"],
        listener: Optional[ConsumerRebalanceListener],
    ):
        self.consumer = consumer
        self.logger = logger
        self.listener = listener
        self._log_unassigned_consumer_task: Optional[asyncio.Task[None]] = None

    async def log_unassigned_consumer(self) -> None:
        await asyncio.sleep(self._log_unassigned_consumer_delay_seconds)
        self._log(
            logging.WARNING,
            f"Consumer in group {self.consumer._group_id} has had no partition "
            f"assignments for {self._log_unassigned_consumer_delay_seconds} seconds: "
            f"topics {self.consumer._subscription.topics} may have fewer partitions "
            f"than consumers.",
        )

    async def on_partitions_revoked(self, revoked: Set["TopicPartition"]) -> None:
        if self.listener:
            call_result = self.listener.on_partitions_revoked(revoked)
            if asyncio.iscoroutine(call_result):
                await call_result

    async def on_partitions_assigned(self, assigned: Set["TopicPartition"]) -> None:
        self._log(
            logging.INFO,
            f"Consumer {self.consumer._coordinator.member_id} assigned to partitions: "
            f"{assigned}",
        )
        if not assigned:
            self._log(
                logging.WARNING,
                f"Consumer in group {self.consumer._group_id} has no partition assignments - this "
                f"could be temporary, e.g. during a rolling update. A separate warning will be logged if "
                f"this condition persists for {self._log_unassigned_consumer_delay_seconds} seconds.",
            )
            self._log_unassigned_consumer_task = asyncio.create_task(
                self.log_unassigned_consumer()
            )
        elif self._log_unassigned_consumer_task:
            self._log_unassigned_consumer_task.cancel()
            self._log_unassigned_consumer_task = None

        if self.listener:
            call_result = self.listener.on_partitions_assigned(assigned)
            if asyncio.iscoroutine(call_result):
                await call_result

    def _log(
        self,
        log_level: int,
        message: str,
        extra: Optional["AnyDict"] = None,
        exc_info: Optional[Exception] = None,
    ) -> None:
        if self.logger is not None:
            self.logger.log(
                log_level,
                message,
                extra=extra,
                exc_info=exc_info,
            )
