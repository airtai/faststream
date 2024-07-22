from enum import Enum

ContentType = str


class ContentTypes(str, Enum):
    """A class to represent content types."""

    text = "text/plain"
    json = "application/json"


class AsyncAPIVersion(str, Enum):
    v3_0 = "3.0"
    v2_6 = "2.6"
