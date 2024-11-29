"""AsyncAPI related functions."""

from faststream.asyncapi.generate import get_app_schema
from faststream.asyncapi.site import get_asyncapi_html

__all__ = (
    "get_app_schema",
    "get_asyncapi_html",
)
