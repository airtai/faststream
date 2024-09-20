from enum import Enum
from typing import Any

ContentType = str


class ContentTypes(str, Enum):
    """A class to represent content types."""

    text = "text/plain"
    json = "application/json"


class EmptyPlaceholder:
    def __repr__(self) -> str:
        return "EMPTY"

    def __bool__(self) -> bool:
        return False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EmptyPlaceholder):
            return NotImplemented

        return True


EMPTY: Any = EmptyPlaceholder()
