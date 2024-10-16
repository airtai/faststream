from typing import Optional

from faststream._internal.proto import NameProxy
from faststream._internal.utils.path import compile_path


class PubSub(NameProxy):
    """A class to represent a Redis PubSub channel."""

    _pattern: str
    __slots__ = (
        "_prefix",
        "_value",
        "_pattern",
        "_channel",
        "polling_interval",
        "path_regex",
    )

    def __init__(
        self,
        channel: Optional[str] = None,
        polling_interval: float = 1.0,
    ) -> None:
        if not channel:
            channel = ""
        reg, path = compile_path(
            channel,
            replace_symbol="*",
            patch_regex=lambda x: x.replace(r"\*", ".*"),
        )

        super().__init__(path)
        self._channel = channel
        self._pattern = ""
        self.path_regex = reg
        self.polling_interval = polling_interval

    @property
    def pattern(self) -> str:
        if self._pattern is None:
            raise ValueError
        return self._pattern

    @pattern.setter
    def pattern(self, pattern: bool = False) -> None:
        if self.path_regex:
            pattern = True
        self._pattern = self._channel if pattern else None
