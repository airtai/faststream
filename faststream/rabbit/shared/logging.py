import logging
from typing import Any, Optional

from faststream._compat import override
from faststream.broker.core.mixins import LoggingMixin
from faststream.broker.message import StreamMessage
from faststream.log import access_logger
from faststream.rabbit.shared.schemas import RabbitExchange, RabbitQueue
from faststream.types import AnyDict


class RabbitLoggingMixin(LoggingMixin):
    _max_queue_len: int
    _max_exchange_len: int

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
        self._max_queue_len = 4
        self._max_exchange_len = 4

    @override
    def _get_log_context(  # type: ignore[override]
        self,
        message: Optional[StreamMessage[Any]],
        queue: RabbitQueue,
        exchange: Optional[RabbitExchange] = None,
    ) -> AnyDict:
        context = {
            "queue": queue.name,
            "exchange": exchange.name if exchange else "default",
            **super()._get_log_context(message),
        }
        return context

    @property
    def fmt(self) -> str:
        return super().fmt or (
            "%(asctime)s %(levelname)s - "
            f"%(exchange)-{self._max_exchange_len}s | "
            f"%(queue)-{self._max_queue_len}s | "
            f"%(message_id)-10s "
            "- %(message)s"
        )

    def _setup_log_context(
        self,
        queue: Optional[RabbitQueue] = None,
        exchange: Optional[RabbitExchange] = None,
    ) -> None:
        if exchange is not None:
            self._max_exchange_len = max(
                self._max_exchange_len, len(exchange.name or "")
            )

        if queue is not None:  # pragma: no branch
            self._max_queue_len = max(self._max_queue_len, len(queue.name))
