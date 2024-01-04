import warnings
from typing import Optional, Pattern

from pydantic import Field, PositiveFloat, PositiveInt

from faststream._compat import PYDANTIC_V2
from faststream.broker.schemas import NameRequired
from faststream.utils.path import compile_path


class PubSub(NameRequired):
    """A class to represent a Redis PubSub channel."""

    polling_interval: PositiveFloat = 1.0
    path_regex: Optional[Pattern[str]] = None
    pattern: bool = False
    last_id: str = "$"

    def __init__(
        self,
        channel: str,
        pattern: bool = False,
        polling_interval: PositiveFloat = 1.0,
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

        super().__init__(
            name=path,
            path_regex=reg,
            pattern=pattern,
            polling_interval=polling_interval,
        )

    if PYDANTIC_V2:
        model_config = {"arbitrary_types_allowed": True}
    else:

        class Config:
            arbitrary_types_allowed = True

    def __hash__(self) -> int:
        return hash("pubsub" + self.name)


class ListSub(NameRequired):
    """A class to represent a Redis List subscriber."""

    polling_interval: PositiveFloat = 0.1
    batch: bool = False
    max_records: PositiveInt = 10

    def __init__(
        self,
        channel: str,
        batch: bool = False,
        max_records: PositiveInt = 10,
        polling_interval: PositiveFloat = 0.1,
    ) -> None:
        """Redis List subscriber parameters.

        Args:
            channel: (str): Redis List name.
            batch: (bool): consume messages in batches.
            max_records: (int): max records per batch.
            polling_interval: (float): wait message block.
        """
        super().__init__(
            name=channel,
            batch=batch,
            max_records=max_records,
            polling_interval=polling_interval,
        )

    @property
    def records(self) -> Optional[PositiveInt]:
        return self.max_records if self.batch else None

    def __hash__(self) -> int:
        return hash("list" + self.name)


class StreamSub(NameRequired):
    """A class to represent a Redis Stream subscriber."""

    polling_interval: Optional[PositiveInt] = Field(default=100, description="ms")
    group: Optional[str] = None
    consumer: Optional[str] = None
    batch: bool = False
    no_ack: bool = False
    last_id: str = "$"

    def __init__(
        self,
        stream: str,
        polling_interval: Optional[PositiveInt] = 100,
        group: Optional[str] = None,
        consumer: Optional[str] = None,
        batch: bool = False,
        no_ack: bool = False,
        last_id: Optional[str] = None,
    ) -> None:
        """Redis Stream subscriber parameters.

        Args:
            stream: (str): Redis Stream name.
            polling_interval: (int:ms | None): wait message block.
            group: (str | None): consumer group name.
            consumer: (str | None): consumer name.
            batch: (bool): consume messages in batches.
            no_ack: (bool): do not add message to PEL.
            last_id: (str | None): start reading from this ID.
        """
        if (group and not consumer) or (not group and consumer):
            raise ValueError("You should specify `group` and `consumer` both")

        if group and consumer:
            msg: Optional[str] = None

            if last_id:
                msg = "`last_id` has no effect with consumer group"

            if no_ack:
                msg = "`no_ack` has no effect with consumer group"

            if msg:
                warnings.warn(
                    message=msg,
                    category=RuntimeWarning,
                    stacklevel=1,
                )

        super().__init__(
            name=stream,
            group=group,
            consumer=consumer,
            polling_interval=polling_interval,
            batch=batch,
            no_ack=no_ack,
            last_id=last_id or "$",
        )

    def __hash__(self) -> int:
        return hash("stream" + self.name)


INCORRECT_SETUP_MSG = "You have to specify `channel`, `list` or `stream`"
