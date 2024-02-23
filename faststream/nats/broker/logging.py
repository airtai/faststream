import logging
from inspect import Parameter
from typing import Any, ClassVar, Optional, Union

from faststream.broker.core.logging_mixin import LoggingMixin
from faststream.log.logging import get_broker_logger


class NatsLoggingMixin(LoggingMixin):
    """A class to represent a NATS logging mixin."""

    _max_queue_len: int
    _max_subject_len: int
    __max_msg_id_ln: ClassVar[int] = 10

    def __init__(
        self,
        *args: Any,
        logger: Union[logging.Logger, object, None] = Parameter.empty,
        log_level: int = logging.INFO,
        log_fmt: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the NATS logging mixin.

        Args:
            *args: The arguments.
            logger: The logger.
            log_level: The log level.
            log_fmt: The log format.
            **kwargs: The keyword arguments.
        """
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
        queue: Optional[str] = None,
        subject: Optional[str] = None,
        stream: Optional[str] = None,
    ) -> None:
        self._max_subject_len = max((self._max_subject_len, len(subject or "")))
        self._max_queue_len = max((self._max_queue_len, len(queue or "")))
        self._max_stream_len = max((self._max_stream_len, len(stream or "")))
