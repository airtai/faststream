from typing import TYPE_CHECKING

from faststream._compat import HAS_FASTAPI
from faststream.asyncapi.base import BaseSchema
from faststream.asyncapi.schema import (
    BaseSchema,
)
from faststream.asyncapi.v2_6_0.generate import get_app_schema as get_app_schema_v2_6
from faststream.asyncapi.v3_0_0.generate import get_app_schema as get_app_schema_v3
from faststream.asyncapi.version import AsyncAPIVersion

if TYPE_CHECKING:
    from faststream._compat import HAS_FASTAPI

    if HAS_FASTAPI:
        pass


def get_app_schema(app: "AsyncAPIApplication") -> BaseSchema:
    if app.asyncapi_version == AsyncAPIVersion.v3_0:
        return get_app_schema_v3(app)

    if app.asyncapi_version == AsyncAPIVersion.v2_6:
        return get_app_schema_v2_6(app)

    raise NotImplementedError(f"Async API version not supported: {app.asyncapi_version}")
