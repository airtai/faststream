from abc import abstractmethod
import logging
from inspect import Parameter
from typing import Any, Optional, Union, cast

from faststream.types import AnyDict


class LoggingMixin:
    """A mixin class for logging.

    Attributes:
        logger : logger object used for logging
        log_level : log level for logging
        _fmt : format string for log messages

    Methods:
        fmt : getter method for _fmt attribute
        _log : logs a message with optional log level, extra data, and exception info
    """

    logger: Optional[logging.Logger]

    def __init__(
        self,
        *args: Any,
        default_logger: logging.Logger,
        logger: Union[logging.Logger, None, object],
        log_level: int,
        log_fmt: Optional[str],
        **kwargs: Any,
    ) -> None:
        """Initialize the class.

        Args:
            *args: Variable length argument list
            logger: Optional logger object
            log_level: Log level (default: logging.INFO)
            log_fmt: Log format (default: "%(asctime)s %(levelname)s - %(message)s")
            **kwargs: Arbitrary keyword arguments

        Returns:
            None
        """
        if logger is not Parameter.empty:
            self.logger = cast(Optional[logging.Logger], logger)
            self.use_custom = True
        else:
            self.logger = default_logger
            self.use_custom = False

        self._msg_log_level = log_level
        self._fmt = log_fmt

    @property
    def fmt(self) -> str:
        """Getter method for _fmt attribute."""
        return self._fmt or self.get_fmt()

    @abstractmethod
    def get_fmt(self) -> str:
        raise NotImplementedError()

    def _log(
        self,
        message: str,
        log_level: Optional[int] = None,
        extra: Optional[AnyDict] = None,
        exc_info: Optional[Exception] = None,
    ) -> None:
        """Logs a message.

        Args:
            message: The message to be logged.
            log_level: The log level of the message. If not provided, the default log level of the logger will be used.
            extra: Additional information to be logged along with the message. This should be a dictionary.
            exc_info: An exception to be logged along with the message.

        Returns:
            None
        """
        if self.logger is not None:
            self.logger.log(
                (log_level or self._msg_log_level),
                message,
                extra=extra,
                exc_info=exc_info,
            )
