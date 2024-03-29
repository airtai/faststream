import logging
from inspect import Parameter
from typing import Any, Callable, Optional

from fastapi import params
from typing_extensions import Annotated

from faststream.utils.context import ContextRepo as CR
from faststream.utils.context.types import resolve_context_by_name


def Context(  # noqa: N802
    name: str,
    *,
    default: Any = Parameter.empty,
    initial: Optional[Callable[..., Any]] = None,
) -> Any:
    """Get access to objects of the Context."""
    return params.Depends(
        lambda: resolve_context_by_name(
            name=name,
            default=default,
            initial=initial,
        ),
        use_cache=True,
    )


Logger = Annotated[logging.Logger, Context("logger")]
ContextRepo = Annotated[CR, Context("context")]
