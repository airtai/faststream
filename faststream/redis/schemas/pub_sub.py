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
        return hash(f"pubsub:{self.name}")
