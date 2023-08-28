import logging
from typing import Any, Optional

from faststream.broker.message import StreamMessage
from faststream.broker.types import MsgType
from faststream.log import access_logger
from faststream.types import AnyDict


class LoggingMixin:
    def __init__(
        self,
        *args: Any,
        logger: Optional[logging.Logger] = access_logger,
        log_level: int = logging.INFO,
        log_fmt: Optional[str] = "%(asctime)s %(levelname)s - %(message)s",
        **kwargs: Any,
    ) -> None:
        self.logger = logger
        self.log_level = log_level
        self._fmt = log_fmt

    @property
    def fmt(self) -> str:  # pragma: no cover
        return self._fmt or ""

    def _get_log_context(
        self,
        message: Optional[StreamMessage[MsgType]],
        **kwargs: str,
    ) -> AnyDict:
        return {
            "message_id": message.message_id[:10] if message else "",
        }

    def _log(
        self,
        message: str,
        log_level: Optional[int] = None,
        extra: Optional[AnyDict] = None,
        exc_info: Optional[Exception] = None,
    ) -> None:
        if self.logger is not None:
            self.logger.log(
                level=(log_level or self.log_level),
                msg=message,
                extra=extra,
                exc_info=exc_info,
            )
