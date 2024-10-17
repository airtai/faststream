from functools import partial
from typing import TYPE_CHECKING, Optional

from faststream._internal.log.logging import get_broker_logger
from faststream._internal.setup.logger import (
    DefaultLoggerStorage,
    make_logger_state,
)

if TYPE_CHECKING:
    from faststream._internal.basic_types import AnyDict, LoggerProto


class RabbitParamsStorage(DefaultLoggerStorage):
    def __init__(
        self,
        log_fmt: Optional[str],
    ) -> None:
        super().__init__(log_fmt)

        self._max_exchange_len = 4
        self._max_queue_len = 4

    def setup_log_contest(self, params: "AnyDict") -> None:
        self._max_exchange_len = max(
            self._max_exchange_len,
            len(params.get("exchange", "")),
        )
        self._max_queue_len = max(
            self._max_queue_len,
            len(params.get("queue", "")),
        )

    def get_logger(self) -> "LoggerProto":
        message_id_ln = 10

        # TODO: generate unique logger names to not share between brokers
        return get_broker_logger(
            name="rabbit",
            default_context={
                "queue": "",
                "exchange": "",
            },
            message_id_ln=message_id_ln,
            fmt=self._log_fmt
            or (
                "%(asctime)s %(levelname)-8s - "
                f"%(exchange)-{self._max_exchange_len}s | "
                f"%(queue)-{self._max_queue_len}s | "
                f"%(message_id)-{message_id_ln}s "
                "- %(message)s"
            ),
        )


make_rabbit_logger_state = partial(
    make_logger_state,
    default_storag_cls=RabbitParamsStorage,
)
