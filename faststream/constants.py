from enum import Enum

ContentType = str


class ContentTypes(str, Enum):
    """A class to represent content types."""

    text = "text/plain"
    json = "application/json"
