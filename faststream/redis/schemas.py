from typing import Optional, Pattern

from pydantic import Field, PositiveFloat, PositiveInt

from faststream._compat import PYDANTIC_V2
from faststream.broker.schemas import NameRequired
from faststream.utils.context.path import compile_path


class PubSub(NameRequired):
    polling_interval: PositiveFloat = 1.0
    path_regex: Optional[Pattern[str]] = None
    pattern: bool = False

    def __init__(
        self,
        channel: str,
        pattern: bool = False,
        polling_interval: PositiveFloat = 1.0,
    ) -> None:
        reg, path = compile_path(channel, replace_symbol="*")

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
    polling_interval: Optional[PositiveInt] = Field(default=100, description="ms")
    group: Optional[str] = None
    consumer: Optional[str] = None
    batch: bool = False
    no_ack: bool = False

    def __init__(
        self,
        stream: str,
        polling_interval: Optional[PositiveInt] = 100,
        group: Optional[str] = None,
        consumer: Optional[str] = None,
        batch: bool = False,
        no_ack: bool = False,
    ) -> None:
        """
        Redis Stream subscriber parameters

        Args:
            stream: (str): Redis Stream name.
            polling_interval: (int:ms | None): wait message block.
            group: (str | None): consumer group name.
            consumer: (str | None): consumer name.
            batch: (bool): consume messages in batches.
            no_ack: (bool): do not add message to PEL.
        """
        if (group and not consumer) or (not group and consumer):
            raise ValueError("You should specify `group` and `consumer` both")

        super().__init__(
            name=stream,
            group=group,
            consumer=consumer,
            polling_interval=polling_interval,
            batch=batch,
        )

    def __hash__(self) -> int:
        return hash("stream" + self.name)


INCORRECT_SETUP_MSG = "You have to specify `channel`, `list` or `stream`"
