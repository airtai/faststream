from inspect import _empty
from typing import Any

from faststream.utils.context.types import Context as Context_


def Context(
    real_name: str = "",
    *,
    cast: bool = False,
    default: Any = _empty,
) -> Any:
    return Context_(
        real_name=real_name,
        cast=cast,
        default=default,
    )


def Header(
    real_name: str = "",
    *,
    cast: bool = True,
    default: Any = _empty,
) -> Any:
    return Context_(
        real_name=real_name,
        cast=cast,
        default=default,
        prefix="message.headers.",
    )


def Path(
    real_name: str = "",
    *,
    cast: bool = True,
    default: Any = _empty,
) -> Any:
    return Context_(
        real_name=real_name,
        cast=cast,
        default=default,
        prefix="message.path.",
    )
