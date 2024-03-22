import logging
from inspect import Parameter
from typing import Any, ClassVar, Optional, Union

from faststream.broker.core.logging_mixin import LoggingMixin
from faststream.log.logging import get_broker_logger


class RedisLoggingMixin(LoggingMixin):
    """A class to represent a Redis logging mixin."""

    _max_channel_name: int
    __max_msg_id_ln: ClassVar[int] = 10

    def __init__(
        self,
        *args: Any,
        logger: Union[logging.Logger, object, None] = Parameter.empty,
        log_level: int = logging.INFO,
        log_fmt: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the class.

        Args:
            *args: Variable length argument list
            logger: Optional logger object
            log_level: Logging level
            log_fmt: Optional log format
            **kwargs: Arbitrary keyword arguments

        Returns:
            None
        """
        super().__init__(
            *args,
            logger=logger,
            # TODO: generate unique logger names to not share between brokers
            default_logger=get_broker_logger(
                name="redis",
                default_context={
                    "channel": "",
                },
                message_id_ln=self.__max_msg_id_ln,
            ),
            log_level=log_level,
            log_fmt=log_fmt,
            **kwargs,
        )
        self._max_channel_name = 4

    def get_fmt(self) -> str:
        return (
            "%(asctime)s %(levelname)-8s - "
            f"%(channel)-{self._max_channel_name}s | "
            f"%(message_id)-{self.__max_msg_id_ln}s "
            "- %(message)s"
        )

    def _setup_log_context(
        self,
        channel: Optional[str] = None,
    ) -> None:
        self._max_channel_name = max((self._max_channel_name, len(channel or "")))
