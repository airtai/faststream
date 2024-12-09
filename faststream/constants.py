from enum import Enum, auto

ContentType = str


class ContentTypes(str, Enum):
    """A class to represent content types."""

    text = "text/plain"
    json = "application/json"


class AppState(str, Enum):
    """Class with application states."""

    STATE_STOPPED = auto()
    STATE_RUNNING = auto()
