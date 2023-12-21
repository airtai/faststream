import logging
from inspect import _empty
from typing import Any, Callable, Optional

from fastapi import params

from faststream._compat import Annotated
from faststream.utils.context import ContextRepo as CR
from faststream.utils.context.types import resolve_context_by_name


def Context(
    name: str,
    *,
    default: Any = _empty,
    initial: Optional[Callable[..., Any]] = None,
) -> Any:
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
