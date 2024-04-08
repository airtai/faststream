import logging
from collections import defaultdict
from enum import Enum
from typing import TYPE_CHECKING, DefaultDict, Optional, Union

if TYPE_CHECKING:
    from faststream.app import FastStream
    from faststream.types import LoggerProto


class LogLevels(str, Enum):
    """A class to represent log levels.

    Attributes:
        critical : critical log level
        error : error log level
        warning : warning log level
        info : info log level
        debug : debug log level
    """

    critical = "critical"
    error = "error"
    warning = "warning"
    info = "info"
    debug = "debug"


LOG_LEVELS: DefaultDict[str, int] = defaultdict(
    lambda: logging.INFO,
    **{
        "critical": logging.CRITICAL,
        "error": logging.ERROR,
        "warning": logging.WARNING,
        "info": logging.INFO,
        "debug": logging.DEBUG,
    },
)


def get_log_level(level: Union[LogLevels, str, int]) -> int:
    """Get the log level.

    Args:
        level: The log level to get. Can be an integer, a LogLevels enum value, or a string.

    Returns:
        The log level as an integer.

    """
    if isinstance(level, int):
        return level

    if isinstance(level, LogLevels):
        return LOG_LEVELS[level.value]

    if isinstance(level, str):  # pragma: no branch
        return LOG_LEVELS[level.lower()]


def set_log_level(level: int, app: "FastStream") -> None:
    """Sets the log level for an application."""
    if app.logger and isinstance(app.logger, logging.Logger):
        app.logger.setLevel(level)

    broker_logger: Optional["LoggerProto"] = getattr(app.broker, "logger", None)
    if broker_logger is not None and isinstance(broker_logger, logging.Logger):
        broker_logger.setLevel(level)
