from typing import TYPE_CHECKING, Any, Callable, Optional

from faststream._internal.constants import EMPTY

if TYPE_CHECKING:
    from .repository import ContextRepo


def resolve_context_by_name(
    name: str,
    default: Any,
    initial: Optional[Callable[..., Any]],
    context: "ContextRepo",
) -> Any:
    value: Any = EMPTY

    try:
        value = context.resolve(name)

    except (KeyError, AttributeError):
        if EMPTY != default:  # noqa: SIM300
            value = default

        elif initial is not None:
            value = initial()
            context.set_global(name, value)

    return value
