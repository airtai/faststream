from typing import Optional

from faststream._internal.proto import NameProxy
from faststream._internal.utils.path import compile_path


class PubSub(NameProxy):
    """A class to represent a Redis PubSub channel."""

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
        super().__init__(channel)
        self._channel = channel
        self._pattern = None
        self.path_regex = None
        self.polling_interval = polling_interval

    @property
    def pattern(self) -> str:
        if self._channel:  # в теории можно опираться на self.name и проверка не нужна
            reg, path = compile_path(
                self._channel,
                replace_symbol="*",
                patch_regex=lambda x: x.replace(r"\*", ".*"),
            )

            self.name = path
            self.path_regex = reg

            if reg and not self._pattern:
                self._pattern = self._channel
        return self._pattern

    @pattern.setter
    def pattern(self, pattern: bool = False) -> None:
        # вызывается раньше get-свойства, поэтому такой код
        self._pattern = self._channel if pattern else None
