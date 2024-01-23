import logging
from inspect import Parameter
from typing import TYPE_CHECKING, Any, ClassVar, Optional, Union

from faststream.broker.core.logging_mixin import LoggingMixin
from faststream.log.logging import get_broker_logger

if TYPE_CHECKING:
    from faststream.rabbit.schemas.schemas import RabbitExchange, RabbitQueue


class RabbitLoggingMixin(LoggingMixin):
    """A class that extends the LoggingMixin class and adds additional functionality for logging RabbitMQ related information.

    Attributes:
        _max_queue_len : maximum length of the queue name
        _max_exchange_len : maximum length of the exchange name

    Methods:
        __init__ : Initializes the RabbitLoggingMixin object.
        _get_log_context : Overrides the _get_log_context method of the LoggingMixin class to include RabbitMQ related context information.
        fmt : Returns the log format string.
        _setup_log_context : Sets up the log context by updating the maximum lengths of the queue and exchange names.
    """

    _max_queue_len: int
    _max_exchange_len: int
    __max_msg_id_ln: ClassVar[int] = 10

    def __init__(
        self,
        *args: Any,
        logger: Union[logging.Logger, object, None] = Parameter.empty,
        log_level: int = logging.INFO,
        log_fmt: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the class.

        Args:
            *args: Variable length argument list
            logger: Optional logger object
            log_level: Logging level
            log_fmt: Optional log format
            **kwargs: Arbitrary keyword arguments

        Returns:
            None
        """
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

    @property
    def fmt(self) -> str:
        return super().fmt or (
            "%(asctime)s %(levelname)s - "
            f"%(exchange)-{self._max_exchange_len}s | "
            f"%(queue)-{self._max_queue_len}s | "
            f"%(message_id)-{self.__max_msg_id_ln}s "
            "- %(message)s"
        )

    def _setup_log_context(
        self,
        queue: Optional["RabbitQueue"] = None,
        exchange: Optional["RabbitExchange"] = None,
    ) -> None:
        """Set up log context.

        Args:
            queue: Optional RabbitQueue object representing the queue.
            exchange: Optional RabbitExchange object representing the exchange.
        """
        self._max_exchange_len = max(
            self._max_exchange_len,
            len(getattr(exchange, "name", "")),
        )

        self._max_queue_len = max(
            self._max_queue_len,
            len(getattr(queue, "name", "")),
        )