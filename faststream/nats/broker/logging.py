from functools import partial
from typing import TYPE_CHECKING, Optional

from faststream._internal.log.logging import get_broker_logger
from faststream._internal.setup.logger import (
    DefaultLoggerStorage,
    make_logger_state,
)

if TYPE_CHECKING:
    from faststream._internal.basic_types import AnyDict, LoggerProto


class NatsParamsStorage(DefaultLoggerStorage):
    def __init__(
        self,
        log_fmt: Optional[str],
    ) -> None:
        super().__init__(log_fmt)

        self._max_queue_len = 0
        self._max_stream_len = 0
        self._max_subject_len = 4

    def setup_log_contest(self, params: "AnyDict") -> None:
        self._max_subject_len = max(
            (
                self._max_subject_len,
                len(params.get("subject", "")),
            ),
        )
        self._max_queue_len = max(
            (
                self._max_queue_len,
                len(params.get("queue", "")),
            ),
        )
        self._max_stream_len = max(
            (
                self._max_stream_len,
                len(params.get("stream", "")),
            ),
        )

    def get_logger(self) -> Optional["LoggerProto"]:
        message_id_ln = 10

        # TODO: generate unique logger names to not share between brokers
        return get_broker_logger(
            name="nats",
            default_context={
                "subject": "",
                "stream": "",
                "queue": "",
            },
            message_id_ln=message_id_ln,
            fmt=self._log_fmt
            or "".join((
                "%(asctime)s %(levelname)-8s - ",
                (
                    f"%(stream)-{self._max_stream_len}s | "
                    if self._max_stream_len
                    else ""
                ),
                (f"%(queue)-{self._max_queue_len}s | " if self._max_queue_len else ""),
                f"%(subject)-{self._max_subject_len}s | ",
                f"%(message_id)-{message_id_ln}s - ",
                "%(message)s",
            )),
        )


make_nats_logger_state = partial(
    make_logger_state,
    default_storag_cls=NatsParamsStorage,
)
