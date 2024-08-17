from typing import TYPE_CHECKING

from faststream.specification.asyncapi.base.schema import BaseSchema
from faststream.specification.asyncapi.v2_6_0.generate import (
    get_app_schema as get_app_schema_v2_6,
)
from faststream.specification.asyncapi.v3_0_0.generate import (
    get_app_schema as get_app_schema_v3,
)
from faststream.specification.asyncapi.version import AsyncAPIVersion

if TYPE_CHECKING:
    from faststream.specification.proto import Application


def get_app_schema(app: "Application", version: AsyncAPIVersion) -> BaseSchema:
    if version == AsyncAPIVersion.v3_0:
        return get_app_schema_v3(app)

    if version == AsyncAPIVersion.v2_6:
        return get_app_schema_v2_6(app)

    raise NotImplementedError(f"AsyncAPI version not supported: {app.asyncapi_version}")
