import json
import os
import sys
from importlib.metadata import version as get_version
from typing import Any, Callable, Dict, List, Mapping, Optional, Type, TypeVar, Union

from fast_depends._compat import PYDANTIC_V2 as PYDANTIC_V2
from fast_depends._compat import (  # type: ignore[attr-defined]
    PYDANTIC_VERSION as PYDANTIC_VERSION,
)
from fast_depends._compat import FieldInfo
from packaging.version import parse
from pydantic import BaseModel

if sys.version_info < (3, 12):
    from typing_extensions import TypedDict as TypedDict
    from typing_extensions import Unpack as Unpack
    from typing_extensions import override as override
else:
    from typing import TypedDict as TypedDict
    from typing import Unpack as Unpack
    from typing import override as override

if sys.version_info < (3, 11):
    from typing_extensions import Never as Never
    from typing_extensions import NotRequired as NotRequired
    from typing_extensions import Required as Required
    from typing_extensions import Self as Self
else:
    from typing import Never as Never
    from typing import NotRequired as NotRequired
    from typing import Required as Required
    from typing import Self as Self


if sys.version_info < (3, 10):
    from typing_extensions import Concatenate as Concatenate
    from typing_extensions import ParamSpec as ParamSpec
    from typing_extensions import TypeAlias as TypeAlias
else:
    from typing import Concatenate as Concatenate
    from typing import ParamSpec as ParamSpec
    from typing import TypeAlias as TypeAlias

if sys.version_info < (3, 9):
    from typing_extensions import Annotated as Annotated
else:
    from typing import Annotated as Annotated

from faststream.types import AnyDict

ModelVar = TypeVar("ModelVar", bound=BaseModel)


IS_OPTIMIZED = os.getenv("PYTHONOPTIMIZE", False)

ANYIO_VERSION = parse(get_version("anyio"))
ANYIO_V3 = ANYIO_VERSION.major == 3

try:
    from fastapi import __version__ as FASTAPI_VERSION

    HAS_FASTAPI = True

    major, minor, _ = map(int, FASTAPI_VERSION.split("."))
    FASTAPI_V2 = major > 0 or minor > 100

    if FASTAPI_V2:
        from fastapi._compat import _normalize_errors
        from fastapi.exceptions import RequestValidationError

        def raise_fastapi_validation_error(errors: List[Any], body: AnyDict) -> Never:
            raise RequestValidationError(_normalize_errors(errors), body=body)

    else:
        from pydantic import (  # type: ignore[assignment]  # isort: skip
            ValidationError as RequestValidationError,
        )
        from pydantic import create_model

        ROUTER_VALIDATION_ERROR_MODEL = create_model("StreamRoute")

        def raise_fastapi_validation_error(errors: List[Any], body: AnyDict) -> Never:
            raise RequestValidationError(errors, ROUTER_VALIDATION_ERROR_MODEL)  # type: ignore[misc]

except ImportError:
    HAS_FASTAPI = False

JsonSchemaValue = Mapping[str, Any]

if PYDANTIC_V2:
    if PYDANTIC_VERSION >= "2.4.0":
        from pydantic.annotated_handlers import (
            GetJsonSchemaHandler as GetJsonSchemaHandler,
        )
        from pydantic_core.core_schema import (  # type: ignore[attr-defined]
            with_info_plain_validator_function as with_info_plain_validator_function,
        )
    else:
        from pydantic._internal._annotated_handlers import (  # type: ignore[no-redef]
            GetJsonSchemaHandler as GetJsonSchemaHandler,
        )
        from pydantic_core.core_schema import (
            general_plain_validator_function as with_info_plain_validator_function,
        )

    from pydantic_core import CoreSchema as CoreSchema
    from pydantic_core import to_jsonable_python

    SCHEMA_FIELD = "json_schema_extra"

    def model_to_jsonable(
        model: BaseModel,
        **kwargs: Any,
    ) -> Any:
        return to_jsonable_python(model, **kwargs)

    def dump_json(data: Any) -> str:
        return json.dumps(model_to_jsonable(data))

    def get_model_fields(model: Type[BaseModel]) -> Dict[str, FieldInfo]:
        return model.model_fields

    def model_to_json(model: BaseModel, **kwargs: Any) -> str:
        return model.model_dump_json(**kwargs)

    def model_to_dict(model: BaseModel, **kwargs: Any) -> AnyDict:
        return model.model_dump(**kwargs)

    def model_parse(
        model: Type[ModelVar], data: Union[str, bytes], **kwargs: Any
    ) -> ModelVar:
        return model.model_validate_json(data, **kwargs)

    def model_schema(model: Type[BaseModel], **kwargs: Any) -> AnyDict:
        return model.model_json_schema(**kwargs)

    def model_copy(model: ModelVar, **kwargs: Any) -> ModelVar:
        return model.model_copy(**kwargs)

else:
    from pydantic.json import pydantic_encoder

    GetJsonSchemaHandler = Any  # type: ignore[assignment,misc]
    CoreSchema = Any  # type: ignore[assignment,misc]

    SCHEMA_FIELD = "schema_extra"

    def dump_json(data: Any) -> str:
        return json.dumps(data, default=pydantic_encoder)

    def get_model_fields(model: Type[BaseModel]) -> Dict[str, FieldInfo]:
        return model.__fields__  # type: ignore[return-value]

    def model_to_json(model: BaseModel, **kwargs: Any) -> str:
        return model.json(**kwargs)

    def model_to_dict(model: BaseModel, **kwargs: Any) -> AnyDict:
        return model.dict(**kwargs)

    def model_parse(
        model: Type[ModelVar], data: Union[str, bytes], **kwargs: Any
    ) -> ModelVar:
        return model.parse_raw(data, **kwargs)

    def model_schema(model: Type[BaseModel], **kwargs: Any) -> AnyDict:
        return model.schema(**kwargs)

    def model_to_jsonable(
        model: BaseModel,
        **kwargs: Any,
    ) -> Any:
        return json.loads(model.json(**kwargs))

    def model_copy(model: ModelVar, **kwargs: Any) -> ModelVar:
        return model.copy(**kwargs)

    # TODO: pydantic types misc
    def with_info_plain_validator_function(  # type: ignore[misc]
        function: Callable[..., Any],
        *,
        ref: Optional[str] = None,
        metadata: Any = None,
        serialization: Any = None,
    ) -> JsonSchemaValue:
        return {}


if ANYIO_V3:
    from anyio import ExceptionGroup as ExceptionGroup  # type: ignore[attr-defined]
else:
    ExceptionGroup = ExceptionGroup
