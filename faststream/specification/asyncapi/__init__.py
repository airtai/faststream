"""AsyncAPI related functions."""

from faststream.specification.asyncapi.site import get_asyncapi_html

from .base import AsyncAPIProto
from .factory import AsyncAPI

__all__ = (
    "AsyncAPIProto",
    "AsyncAPI",
    "get_asyncapi_html",
)
