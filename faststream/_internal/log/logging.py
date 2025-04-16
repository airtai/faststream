import logging
import sys
from collections.abc import Mapping
from logging import LogRecord
from typing import TYPE_CHECKING

from faststream._internal.log.formatter import ColourizedFormatter

if TYPE_CHECKING:
    from faststream._internal.context.repository import ContextRepo


logger = logging.getLogger("faststream")
logger.setLevel(logging.INFO)
logger.propagate = False
main_handler = logging.StreamHandler(stream=sys.stderr)
main_handler.setFormatter(
    ColourizedFormatter(
        fmt="%(asctime)s %(levelname)8s - %(message)s",
        use_colors=True,
    ),
)
logger.addHandler(main_handler)


class ExtendedFilter(logging.Filter):
    def __init__(
        self,
        default_context: Mapping[str, str],
        message_id_ln: int,
        context: "ContextRepo",
        name: str = "",
    ) -> None:
        self.default_context = default_context
        self.message_id_ln = message_id_ln
        self.context = context
        super().__init__(name)

    def filter(self, record: LogRecord) -> bool:
        if is_suitable := super().filter(record):
            log_context: Mapping[str, str] = self.context.get_local(
                "log_context",
                self.default_context,
            )

            for k, v in log_context.items():
                value = getattr(record, k, v)
                setattr(record, k, value)

            record.message_id = getattr(record, "message_id", "")[: self.message_id_ln]

        return is_suitable


def get_broker_logger(
    name: str,
    default_context: Mapping[str, str],
    message_id_ln: int,
    fmt: str,
    context: "ContextRepo",
    log_level: int,
) -> logging.Logger:
    logger = logging.getLogger(f"faststream.access.{name}")
    logger.setLevel(log_level)
    logger.propagate = False
    logger.addFilter(ExtendedFilter(default_context, message_id_ln, context=context))
    logger.setLevel(logging.INFO)
    return logger


def set_logger_fmt(
    logger: logging.Logger,
    fmt: str = "%(asctime)s %(levelname)s - %(message)s",
) -> None:
    if _handler_exists(logger):
        return None

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(
        ColourizedFormatter(
            fmt=fmt,
            use_colors=True,
        ),
    )
    logger.addHandler(handler)
    return logger


def _handler_exists(logger: logging.Logger) -> bool:
    # Check if a StreamHandler for sys.stdout already exists in the logger.
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
            return True
    return False
