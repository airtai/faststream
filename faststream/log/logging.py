import logging
import logging.config
from functools import partial
from typing import Any, Type

from faststream.log.formatter import ColourizedFormatter
from faststream.types import AnyDict


def configure_formatter(
    formatter: Type[logging.Formatter], *args: Any, **kwargs: Any
) -> logging.Formatter:
    return formatter(*args, **kwargs)


LOGGING_CONFIG: AnyDict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": partial(configure_formatter, ColourizedFormatter),
            "fmt": "%(asctime)s %(levelname)s - %(message)s",
            "use_colors": True,
        },
        "access": {
            "()": partial(configure_formatter, ColourizedFormatter),
            "fmt": "%(asctime)s %(levelname)s - %(message)s",
            "use_colors": True,
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "faststream": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "faststream.error": {"level": "INFO"},
        "faststream.access": {
            "handlers": ["access"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

logging.config.dictConfig(LOGGING_CONFIG)


logger = logging.getLogger("faststream")
access_logger = logging.getLogger("faststream.access")
