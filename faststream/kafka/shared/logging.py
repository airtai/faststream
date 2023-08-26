import logging
from typing import Any, Iterable, Optional, Sequence

from aiokafka import ConsumerRecord

from faststream._compat import override
from faststream.broker.core.mixins import LoggingMixin
from faststream.broker.message import StreamMessage
from faststream.log import access_logger
from faststream.types import AnyDict


class KafkaLoggingMixin(LoggingMixin):
    _max_topic_len: int

    def __init__(
        self,
        *args: Any,
        logger: Optional[logging.Logger] = access_logger,
        log_level: int = logging.INFO,
        log_fmt: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            *args,
            logger=logger,
            log_level=log_level,
            log_fmt=log_fmt,
            **kwargs,
        )
        self._max_topic_len = 4

    @override
    def _get_log_context(  # type: ignore[override]
        self,
        message: Optional[StreamMessage[ConsumerRecord]],
        topics: Sequence[str] = (),
    ) -> AnyDict:
        if topics:
            topic = ", ".join(topics)
        elif message is not None:
            topic = message.raw_message.topic
        else:
            topic = ""

        context = {
            "topic": topic,
            **super()._get_log_context(message),
        }
        return context

    @property
    def fmt(self) -> str:
        return super().fmt or (
            "%(asctime)s %(levelname)s - "
            f"%(topic)-{self._max_topic_len}s | "
            "%(message_id)-10s "
            "- %(message)s"
        )

    def _setup_log_context(self, topics: Iterable[str]) -> None:
        for t in topics:
            self._max_topic_len = max((self._max_topic_len, len(t)))
