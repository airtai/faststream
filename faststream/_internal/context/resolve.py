from typing import Any, Callable, Optional

from faststream._internal.constants import EMPTY

from .repository import context


def resolve_context_by_name(
    name: str,
    default: Any,
    initial: Optional[Callable[..., Any]],
) -> Any:
    value: Any = EMPTY

    try:
        value = context.resolve(name)

    except (KeyError, AttributeError):
        if default != EMPTY:
            value = default

        elif initial is not None:
            value = initial()
            context.set_global(name, value)

    return value
