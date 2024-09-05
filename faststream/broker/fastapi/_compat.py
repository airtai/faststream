from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, List, Optional

from fastapi import __version__ as FASTAPI_VERSION  # noqa: N812
from fastapi.dependencies.utils import solve_dependencies
from starlette.background import BackgroundTasks
from typing_extensions import Never

from faststream.types import AnyDict

if TYPE_CHECKING:
    from fastapi.dependencies.models import Dependant
    from fastapi.requests import Request

major, minor, patch, *_ = map(int, FASTAPI_VERSION.split("."))
FASTAPI_V2 = major > 0 or minor > 100
FASTAPI_V106 = major > 0 or minor >= 106
FASTAPI_v102_3 = major > 0 or minor > 112 or (minor == 112 and patch > 2)

__all__ = (
    "create_response_field",
    "solve_faststream_dependency",
    "raise_fastapi_validation_error",
    "RequestValidationError",
)


@dataclass
class SolvedDependency:
    values: AnyDict
    errors: List[Any]
    background_tasks: Optional[BackgroundTasks]


if FASTAPI_V2:
    from fastapi._compat import _normalize_errors
    from fastapi.exceptions import RequestValidationError

    def raise_fastapi_validation_error(errors: List[Any], body: AnyDict) -> Never:
        raise RequestValidationError(_normalize_errors(errors), body=body)

else:
    from pydantic import (  # type: ignore[assignment]
        ValidationError as RequestValidationError,
    )
    from pydantic import create_model

    ROUTER_VALIDATION_ERROR_MODEL = create_model("StreamRoute")

    def raise_fastapi_validation_error(errors: List[Any], body: AnyDict) -> Never:
        raise RequestValidationError(errors, ROUTER_VALIDATION_ERROR_MODEL)  # type: ignore[misc]


if FASTAPI_v102_3:
    from fastapi.utils import (
        create_model_field as create_response_field,
    )

    async def solve_faststream_dependency(
        request: "Request",
        dependant: "Dependant",
        dependency_overrides_provider: Optional[Any],
        **kwargs: Any,
    ) -> SolvedDependency:
        solved_result = await solve_dependencies(
            request=request,
            body=request._body,  # type: ignore[arg-type]
            dependant=dependant,
            dependency_overrides_provider=dependency_overrides_provider,
            **kwargs,
        )
        values, errors, background = (
            solved_result.values,
            solved_result.errors,
            solved_result.background_tasks,
        )

        return SolvedDependency(
            values=values,
            errors=errors,
            background_tasks=background,
        )

else:
    from fastapi.utils import (  # type: ignore[attr-defined,no-redef]
        create_response_field as create_response_field,
    )

    async def solve_faststream_dependency(
        request: "Request",
        dependant: "Dependant",
        dependency_overrides_provider: Optional[Any],
        **kwargs: Any,
    ) -> SolvedDependency:
        solved_result = await solve_dependencies(
            request=request,
            body=request._body,  # type: ignore[arg-type]
            dependant=dependant,
            dependency_overrides_provider=dependency_overrides_provider,
            **kwargs,
        )

        (
            values,
            errors,
            background,
            _response,
            _dependency_cache,
        ) = solved_result  # type: ignore[misc]

        return SolvedDependency(
            values=values,  # type: ignore[has-type]
            errors=errors,  # type: ignore[has-type]
            background_tasks=background,  # type: ignore[has-type]
        )
