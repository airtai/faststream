"""AsyncAPI related functions."""

from faststream.specification.asyncapi.generate import get_app_schema
from faststream.specification.asyncapi.site import get_asyncapi_html

__all__ = (
    "get_asyncapi_html",
    "get_app_schema",
)
