from typing import Optional, Pattern

from faststream._compat import PYDANTIC_V2
from faststream.broker.schemas import NameRequired
from faststream.utils.context.path import compile_path


class PubSub(NameRequired):
    polling_interval: float = 1.0
    path_regex: Optional[Pattern[str]] = None
    pattern: bool = False

    def __init__(
        self,
        channel: str,
        pattern: bool = False,
        polling_interval: float = 1.0,
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
    polling_interval: float = 0.1
    batch: bool = False
    max_records: int = 10

    def __init__(
        self,
        channel: str,
        batch: bool = False,
        max_records: int = 10,
        polling_interval: float = 0.1,
    ) -> None:
        super().__init__(
            name=channel,
            batch=batch,
            max_records=max_records,
            polling_interval=polling_interval,
        )

    @property
    def records(self) -> Optional[int]:
        return self.max_records if self.batch else None
    
    def __hash__(self) -> int:
        return hash("list" + self.name)


INCORRECT_SETUP_MSG = "You have to specify `channel` or `list`"
