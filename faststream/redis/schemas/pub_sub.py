from typing import Optional

from faststream._internal.proto import NameProxy
from faststream._internal.utils.path import compile_path


class PubSub(NameProxy):
    """A class to represent a Redis PubSub channel."""

    __slots__ = (
        "channel",
        "polling_interval",
        "pattern",
        "path_regex",
    )

    def __init__(
        self,
        channel: Optional[str] = None,
        pattern: bool = False,
        polling_interval: float = 1.0,
    ) -> None:
        if channel is None:
            channel = ""
        reg, path = compile_path(
            channel,
            replace_symbol="*",
            patch_regex=lambda x: x.replace(r"\*", ".*"),
        )

        if reg is not None:
            pattern = True

        super().__init__(path)

        self.path_regex = reg
        self.pattern = channel if pattern else None
        self.polling_interval = polling_interval
