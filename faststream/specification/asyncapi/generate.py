from typing import TYPE_CHECKING, Literal, Union

from faststream.specification.asyncapi.base.schema import BaseSchema
from faststream.specification.asyncapi.v2_6_0.generate import (
    get_app_schema as get_app_schema_v2_6,
)
from faststream.specification.asyncapi.v3_0_0.generate import (
    get_app_schema as get_app_schema_v3,
)

if TYPE_CHECKING:
    from faststream.specification.proto import SpecApplication


def get_app_schema(
    app: "SpecApplication",
    version: Union[Literal["3.0.0", "2.6.0"], str] = "3.0.0",
) -> BaseSchema:
    if version.startswith("3.0."):
        return get_app_schema_v3(app)

    if version.startswith("2.6."):
        return get_app_schema_v2_6(app)

    raise NotImplementedError(f"AsyncAPI version not supported: {version}")
