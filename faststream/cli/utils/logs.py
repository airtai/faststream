import logging
from collections import defaultdict
from enum import Enum
from typing import DefaultDict, Optional, Union

from faststream.app import FastStream


class LogLevels(str, Enum):
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
    if isinstance(level, int):
        return level

    if isinstance(level, LogLevels):
        return LOG_LEVELS[level.value]

    if isinstance(level, str):  # pragma: no branch
        return LOG_LEVELS[level.lower()]


def set_log_level(level: int, app: FastStream) -> None:
    if app.logger:
        app.logger.setLevel(level)

    broker_logger: Optional[logging.Logger] = getattr(app.broker, "logger", None)
    if broker_logger is not None:
        broker_logger.setLevel(level)
