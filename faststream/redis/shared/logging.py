import logging
from typing import Any, Optional

from typing_extensions import override

from faststream.broker.core.mixins import LoggingMixin
from faststream.broker.message import StreamMessage
from faststream.log import access_logger
from faststream.types import AnyDict


class RedisLoggingMixin(LoggingMixin):
    """A class to represent a Redis logging mixin."""

    _max_channel_name: int

    def __init__(
        self,
        *args: Any,
        logger: Optional[logging.Logger] = access_logger,
        log_level: int = logging.INFO,
        log_fmt: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Redis logging mixin.

        Args:
            *args: The arguments.
            logger: The logger.
            log_level: The log level.
            log_fmt: The log format.
            **kwargs: The keyword arguments.
        """
        super().__init__(
            *args,
            logger=logger,
            log_level=log_level,
            log_fmt=log_fmt,
            **kwargs,
        )
        self._message_id_ln = 15
        self._max_channel_name = 4

    @override
    def _get_log_context(  # type: ignore[override]
        self,
        message: Optional[StreamMessage[Any]],
        channel: str,
    ) -> AnyDict:
        return {
            "channel": channel,
            **super()._get_log_context(message),
        }

    @property
    def fmt(self) -> str:
        return self._fmt or (
            "%(asctime)s %(levelname)s - "
            f"%(channel)-{self._max_channel_name}s | "
            f"%(message_id)-{self._message_id_ln}s - %(message)s"
        )

    def _setup_log_context(
        self,
        channel: Optional[str] = None,
    ) -> None:
        if channel is not None:  # pragma: no branch
            self._max_channel_name = max((self._max_channel_name, len(channel)))
