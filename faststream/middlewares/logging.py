import logging
from typing import TYPE_CHECKING, Any, Optional

from faststream._internal.context.repository import context
from faststream._internal.setup.logger import LoggerState
from faststream.exceptions import IgnoredException

from .base import BaseMiddleware

if TYPE_CHECKING:
    from types import TracebackType

    from faststream.message import StreamMessage


class CriticalLogMiddleware:
    def __init__(self, logger: LoggerState) -> None:
        """Initialize the class."""
        self.logger = logger

    def __call__(self, msg: Optional[Any] = None) -> Any:
        return LoggingMiddleware(logger=self.logger)


class LoggingMiddleware(BaseMiddleware):
    """A middleware class for logging critical errors."""

    def __init__(self, logger: LoggerState) -> None:
        self.logger = logger

    async def on_consume(
        self,
        msg: "StreamMessage[Any]",
    ) -> "StreamMessage[Any]":
        self.logger.log(
            "Received",
            extra=context.get_local("log_context", {}),
        )
        return await super().on_consume(msg)

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exc_tb: Optional["TracebackType"] = None,
    ) -> bool:
        """Asynchronously called after processing."""
        c = context.get_local("log_context", {})

        if exc_type:
            if issubclass(exc_type, IgnoredException):
                self.logger.log(
                    log_level=logging.INFO,
                    message=exc_val,
                    extra=c,
                )
            else:
                self.logger.log(
                    log_level=logging.ERROR,
                    message=f"{exc_type.__name__}: {exc_val}",
                    exc_info=exc_val,
                    extra=c,
                )

        self.logger.log(message="Processed", extra=c)

        await super().after_processed(exc_type, exc_val, exc_tb)

        # Exception was not processed
        return False
