from typing import Optional

from typing_extensions import Annotated, Doc

from faststream.broker.schemas import NameRequired


class KvWatch(NameRequired):
    """A class to represent a NATS kv watch subscription."""

    __slots__ = (
        "bucket",
        "headers_only",
        "include_history",
        "ignore_deletes",
        "meta_only",
        "inactive_threshold",
        "timeout",
        "declare",
    )

    def __init__(
        self,
        bucket: Annotated[
            str,
            Doc("Bucket name."),
        ],
        headers_only: Annotated[
            bool,
            Doc("Whether to receive only headers."),
        ] = False,
        include_history: Annotated[
            bool,
            Doc("Whether to include history."),
        ] = False,
        ignore_deletes: Annotated[
            bool,
            Doc("Whether to ignore deletes."),
        ] = False,
        meta_only: Annotated[
            bool,
            Doc("Whether to receive only metadata."),
        ] = False,
        inactive_threshold: Annotated[
            Optional[float],
            Doc("Inactivity threshold."),
        ] = None,
        timeout: Annotated[
            Optional[float],
            Doc("Timeout in seconds."),
        ] = 5.0,
        # custom
        declare: Annotated[
            bool,
            Doc("Whether to create bucket automatically or just connect to it."),
        ] = True,
    ) -> None:
        super().__init__(bucket)

        self.headers_only = headers_only
        self.include_history = include_history
        self.ignore_deletes = ignore_deletes
        self.meta_only = meta_only
        self.inactive_threshold = inactive_threshold
        self.timeout = timeout

        self.declare = declare

    def __hash__(self) -> int:
        return hash(self.name)
