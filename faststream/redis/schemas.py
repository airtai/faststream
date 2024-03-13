import warnings
from functools import cached_property
from typing import Optional

from faststream.broker.schemas import NameRequired
from faststream.utils.path import compile_path


class PubSub(NameRequired):
    """A class to represent a Redis PubSub channel."""

    __slots__ = (
        "name",
        "polling_interval",
        "pattern",
        "path_regex",
    )

    def __init__(
        self,
        channel: str,
        pattern: bool = False,
        polling_interval: float = 1.0,
    ) -> None:
        """Redis PubSub channel parameters.

        Args:
            channel: (str): Redis PubSub channel name.
            pattern: (bool): use pattern matching.
            polling_interval: (float): wait message block.
        """
        reg, path = compile_path(
            channel,
            replace_symbol="*",
            patch_regex=lambda x: x.replace(r"\*", ".*"),
        )

        if reg is not None:
            pattern = True

        super().__init__(path)

        self.path_regex = reg
        self.pattern = pattern
        self.polling_interval = polling_interval

    def __hash__(self) -> int:
        return hash("pubsub" + self.name)


class ListSub(NameRequired):
    """A class to represent a Redis List subscriber."""

    __slots__ = (
        "name",
        "batch",
        "max_records",
        "polling_interval",
    )

    def __init__(
        self,
        list_name: str,
        batch: bool = False,
        max_records: int = 10,
        polling_interval: float = 0.1,
    ) -> None:
        """Redis List subscriber parameters."""
        super().__init__(list_name)

        self.batch = batch
        self.max_records = max_records
        self.polling_interval = polling_interval

    @cached_property
    def records(self) -> Optional[int]:
        return self.max_records if self.batch else None

    def __hash__(self) -> int:
        return hash("list" + self.name)


class StreamSub(NameRequired):
    """A class to represent a Redis Stream subscriber."""

    __slots__ = (
        "name",
        "polling_interval",
        "last_id",
        "group",
        "consumer",
        "no_ack",
        "batch",
        "max_records",
        "maxlen",
    )

    def __init__(
        self,
        stream: str,
        polling_interval: Optional[int] = 100,
        group: Optional[str] = None,
        consumer: Optional[str] = None,
        batch: bool = False,
        no_ack: bool = False,
        last_id: Optional[str] = None,
        maxlen: Optional[int] = None,
        max_records: Optional[int] = None,
    ) -> None:
        """Redis Stream subscriber parameters."""
        if (group and not consumer) or (not group and consumer):
            raise ValueError("You should specify `group` and `consumer` both")

        if group and consumer and no_ack:
            warnings.warn(
                message="`no_ack` has no effect with consumer group",
                category=RuntimeWarning,
                stacklevel=1,
            )

        if last_id is None:
            last_id = "$"

        super().__init__(stream)

        self.group = group
        self.consumer = consumer
        self.polling_interval = polling_interval
        self.batch = batch
        self.no_ack = no_ack
        self.last_id = last_id
        self.maxlen = maxlen
        self.max_records = max_records

    def __hash__(self) -> int:
        return hash("stream" + self.name)


INCORRECT_SETUP_MSG = "You have to specify `channel`, `list` or `stream`"
