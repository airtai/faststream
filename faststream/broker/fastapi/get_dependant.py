from typing import Any, Callable, Iterable

from fastapi import params
from fastapi.dependencies.models import Dependant
from fastapi.dependencies.utils import get_dependant, get_parameterless_sub_dependant

from faststream._compat import PYDANTIC_V2


def get_fastapi_dependant(
    orig_call: Callable[..., Any],
    dependencies: Iterable[params.Depends],
    path_name: str = ""
) -> Any:
    """Generate FastStream-Compatible FastAPI Dependant object."""
    dependent = get_fastapi_native_dependant(
        orig_call=orig_call,
        dependencies=dependencies,
        path_name=path_name,
    )

    dependent = _patch_fastapi_dependent(dependent)

    return dependent


def get_fastapi_native_dependant(
    orig_call: Callable[..., Any],
    dependencies: Iterable[params.Depends],
    path_name: str = ""
) -> Any:
    """Generate native FastAPI Dependant."""
    dependent = get_dependant(
        path=path_name,
        call=orig_call,
    )

    for depends in list(dependencies)[::-1]:
        dependent.dependencies.insert(
            0,
            get_parameterless_sub_dependant(depends=depends, path=path_name),
        )

    return dependent


def _patch_fastapi_dependent(dependent: Dependant) -> Dependant:
    """Patch FastAPI by adding fields for AsyncAPI schema generation."""
    from pydantic import create_model  # FastAPI always has pydantic

    params = dependent.query_params + dependent.body_params  # type: ignore[attr-defined]

    for d in dependent.dependencies:
        params.extend(d.query_params + d.body_params)  # type: ignore[attr-defined]

    params_unique = {}
    params_names = set()
    for p in params:
        if p.name not in params_names:
            params_names.add(p.name)
            info = p.field_info if PYDANTIC_V2 else p
            params_unique[p.name] = (info.annotation, info.default)  # type: ignore[attr-defined]

    dependent.model = create_model(  # type: ignore[attr-defined,call-overload]
        getattr(dependent.call, "__name__", type(dependent.call).__name__),
        **params_unique,
    )
    dependent.custom_fields = {}  # type: ignore[attr-defined]
    dependent.flat_params = params_unique  # type: ignore[attr-defined,assignment,misc]

    return dependent
