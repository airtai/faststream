import logging
from inspect import Parameter
from typing import TYPE_CHECKING, Any, ClassVar, Optional, Union

from nats.aio.client import Client
from nats.aio.msg import Msg

from faststream.broker.core.usecase import BrokerUsecase
from faststream.log.logging import get_broker_logger

if TYPE_CHECKING:
    from faststream.types import LoggerProto


class NatsLoggingBroker(BrokerUsecase[Msg, Client]):
    """A class that extends the LoggingMixin class and adds additional functionality for logging NATS related information."""

    _max_queue_len: int
    _max_subject_len: int
    __max_msg_id_ln: ClassVar[int] = 10

    def __init__(
        self,
        *args: Any,
        logger: Union["LoggerProto", object, None] = Parameter.empty,
        log_level: int = logging.INFO,
        log_fmt: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the NATS logging mixin."""
        super().__init__(
            *args,
            logger=logger,
            # TODO: generate unique logger names to not share between brokers
            default_logger=get_broker_logger(
                name="nats",
                default_context={
                    "subject": "",
                    "stream": "",
                    "queue": "",
                },
                message_id_ln=self.__max_msg_id_ln,
            ),
            log_level=log_level,
            log_fmt=log_fmt,
            **kwargs,
        )

        self._max_queue_len = 0
        self._max_stream_len = 0
        self._max_subject_len = 4

    def get_fmt(self) -> str:
        """Fallback method to get log format if `log_fmt` if not specified."""
        return (
            "%(asctime)s %(levelname)-8s - "
            + (f"%(stream)-{self._max_stream_len}s | " if self._max_stream_len else "")
            + (f"%(queue)-{self._max_queue_len}s | " if self._max_queue_len else "")
            + f"%(subject)-{self._max_subject_len}s | "
            + f"%(message_id)-{self.__max_msg_id_ln}s - "
            "%(message)s"
        )

    def _setup_log_context(
        self,
        *,
        queue: Optional[str] = None,
        subject: Optional[str] = None,
        stream: Optional[str] = None,
    ) -> None:
        """Setup subscriber's information to generate default log format."""
        self._max_subject_len = max((self._max_subject_len, len(subject or "")))
        self._max_queue_len = max((self._max_queue_len, len(queue or "")))
        self._max_stream_len = max((self._max_stream_len, len(stream or "")))
