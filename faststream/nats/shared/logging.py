import logging
from typing import Any, Optional

from faststream._compat import override
from faststream.broker.core.mixins import LoggingMixin
from faststream.broker.message import StreamMessage
from faststream.log import access_logger
from faststream.types import AnyDict


class NatsLoggingMixin(LoggingMixin):
    _max_queue_len: int
    _max_subject_len: int

    def __init__(
        self,
        *args: Any,
        logger: Optional[logging.Logger] = access_logger,
        log_level: int = logging.INFO,
        log_fmt: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            *args,
            logger=logger,
            log_level=log_level,
            log_fmt=log_fmt,
            **kwargs,
        )
        self._max_queue_len = 0
        self._max_stream_len = 0
        self._max_subject_len = 4

    @override
    def _get_log_context(  # type: ignore[override]
        self,
        message: Optional[StreamMessage[Any]],
        subject: str,
        queue: str = "",
        stream: str = "",
    ) -> AnyDict:
        return {
            "subject": subject,
            "queue": queue,
            "stream": stream,
            **super()._get_log_context(message),
        }

    @property
    def fmt(self) -> str:
        return self._fmt or (
            "%(asctime)s %(levelname)s - "
            + (f"%(stream)-{self._max_stream_len}s | " if self._max_stream_len else "")
            + (f"%(queue)-{self._max_queue_len}s | " if self._max_queue_len else "")
            + f"%(subject)-{self._max_subject_len}s | "
            + f"%(message_id)-{self._message_id_ln}s "
            "- %(message)s"
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
