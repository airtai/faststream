import logging
from typing import Any, Iterable, Optional, ClassVar, Union
from inspect import Parameter

from faststream.log.logging import get_broker_logger
from faststream.broker.core.logging_mixin import LoggingMixin


class KafkaLoggingMixin(LoggingMixin):
    """Confluent-specific logging mixin."""

    _max_topic_len: int
    _max_group_len:  int
    __max_msg_id_ln: ClassVar[int] = 10

    def __init__(
        self,
        *args: Any,
        logger: Union[logging.Logger, object, None] = Parameter.empty,
        log_level: int = logging.INFO,
        log_fmt: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the class."""
        super().__init__(
            *args,
            logger=logger,
            # TODO: generate unique logger names to not share between brokers
            default_logger=get_broker_logger(
                name="kafka",
                default_context={
                    "topic": "",
                    "group_id": "",
                },
                message_id_ln=self.__max_msg_id_ln,
            ),
            log_level=log_level,
            log_fmt=log_fmt,
            **kwargs,
        )
        self._max_topic_len = 4
        self._max_group_len = 0

    def get_fmt(self) -> str:
        return (
            "%(asctime)s %(levelname)-8s - "
            + f"%(topic)-{self._max_topic_len}s | "
            + (f"%(group_id)-{self._max_group_len}s | " if self._max_group_len else "")
            + f"%(message_id)-{self.__max_msg_id_ln}s "
            + "- %(message)s"
        )

    def _setup_log_context(
        self, topics: Iterable[str], group_id: Optional[str] = None
    ) -> None:
        """Set up log context."""
        for t in topics:
            self._max_topic_len = max((self._max_topic_len, len(t)))

        if group_id:
            self._max_group_len = max((self._max_group_len, len(group_id)))
