import logging
from inspect import Parameter
from typing import TYPE_CHECKING, Any, ClassVar, Optional, Union

from aio_pika import IncomingMessage, RobustConnection

from faststream.broker.core.usecase import BrokerUsecase
from faststream.log.logging import get_broker_logger

if TYPE_CHECKING:
    from faststream.types import LoggerProto


class RabbitLoggingBroker(BrokerUsecase[IncomingMessage, RobustConnection]):
    """A class that extends the LoggingMixin class and adds additional functionality for logging RabbitMQ related information."""

    _max_queue_len: int
    _max_exchange_len: int
    __max_msg_id_ln: ClassVar[int] = 10

    def __init__(
        self,
        *args: Any,
        logger: Union["LoggerProto", object, None] = Parameter.empty,
        log_level: int = logging.INFO,
        log_fmt: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            *args,
            logger=logger,
            # TODO: generate unique logger names to not share between brokers
            default_logger=get_broker_logger(
                name="rabbit",
                default_context={
                    "queue": "",
                    "exchange": "",
                },
                message_id_ln=self.__max_msg_id_ln,
            ),
            log_level=log_level,
            log_fmt=log_fmt,
            **kwargs,
        )

        self._max_queue_len = 4
        self._max_exchange_len = 4

    def get_fmt(self) -> str:
        return (
            "%(asctime)s %(levelname)-8s - "
            f"%(exchange)-{self._max_exchange_len}s | "
            f"%(queue)-{self._max_queue_len}s | "
            f"%(message_id)-{self.__max_msg_id_ln}s "
            "- %(message)s"
        )

    def _setup_log_context(
        self,
        *,
        queue: Optional[str] = None,
        exchange: Optional[str] = None,
    ) -> None:
        """Set up log context."""
        self._max_exchange_len = max(self._max_exchange_len, len(exchange or ""))
        self._max_queue_len = max(self._max_queue_len, len(queue or ""))
