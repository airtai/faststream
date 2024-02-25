import logging
from typing import Any, ClassVar, Optional, Union

from typing_extensions import Annotated, Doc

from faststream.broker.core.logging_mixin import LoggingMixin
from faststream.log.logging import get_broker_logger


class NatsLoggingMixin(LoggingMixin):
    """NATS-specific logging mixin."""

    _max_queue_len: int
    _max_subject_len: int
    __max_msg_id_ln: ClassVar[int] = 10

    def __init__(
        self,
        *args: Any,
        logger: Annotated[
            Union[logging.Logger, None, object],
            Doc("User specified logger to pass into Context and log service messages."),
        ],
        log_level: Annotated[
            int,
            Doc("Service messages log level."),
        ],
        log_fmt: Annotated[
            Optional[str],
            Doc("Default logger log format."),
        ],
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
        queue: Annotated[
            Optional[str],
            Doc("Using NATS queue group."),
        ] = None,
        subject: Annotated[
            Optional[str],
            Doc("NATS subject to subscribe."),
        ] = None,
        stream: Annotated[
            Optional[str],
            Doc("NATS stream to subscribe."),
        ] = None,
    ) -> None:
        """Setup subscriber's information to generate default log format."""
        self._max_subject_len = max((self._max_subject_len, len(subject or "")))
        self._max_queue_len = max((self._max_queue_len, len(queue or "")))
        self._max_stream_len = max((self._max_stream_len, len(stream or "")))
