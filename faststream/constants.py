from enum import Enum

ContentType = str


class ContentTypes(str, Enum):
    text = "text/plain"
    json = "application/json"
