from enum import Enum

ContentType = str


class ContentTypes(str, Enum):
    """A class to represent content types.

    Attributes:
        text : content type for plain text
        json : content type for JSON data
    """

    text = "text/plain"
    json = "application/json"
