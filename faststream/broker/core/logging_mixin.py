import logging
from abc import abstractmethod
from inspect import Parameter
from typing import Any, Optional, Union, cast

from typing_extensions import Annotated, Doc

from faststream.types import AnyDict


class LoggingMixin:
    """A mixin class for logging.

    Attributes:
        logger : Logger object used for logging
        use_custom : Whether custom logger is specified
        _msg_log_level : Default service messages log level
        _fmt : Default logger log format

    Methods:
        fmt : Default logger log format getter
        _log : Dogs a message if logger is not None
    """

    logger: Optional[logging.Logger]

    def __init__(
        self,
        *args: Any,
        default_logger: Annotated[
            logging.Logger,
            Doc("Logger object to use if `logger` is not setted."),
        ],
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
        """Initialize the class."""
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
        """Get default logger format at broker startup."""
        return self._fmt or self.get_fmt()

    @abstractmethod
    def get_fmt(self) -> str:
        """Fallback method to get log format if `log_fmt` if not specified."""
        raise NotImplementedError()

    def _log(
        self,
        message: Annotated[
            str,
            Doc("Log message."),
        ],
        log_level: Annotated[
            Optional[int],
            Doc("Log record level. Use `__init__: log_level` option if not specified."),
        ] = None,
        extra: Annotated[
            Optional[AnyDict],
            Doc("Log record extra information."),
        ] = None,
        exc_info: Annotated[
            Optional[Exception],
            Doc("Exception object to log traceback."),
        ] = None,
    ) -> None:
        """Logs a message."""
        if self.logger is not None:
            self.logger.log(
                (log_level or self._msg_log_level),
                message,
                extra=extra,
                exc_info=exc_info,
            )
