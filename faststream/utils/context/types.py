from inspect import _empty
from typing import Any

from fast_depends.library import CustomField

from faststream.types import AnyDict
from faststream.utils.context import context


class Context(CustomField):
    param_name: str

    def __init__(
        self,
        real_name: str = "",
        *,
        cast: bool = False,
        default: Any = _empty,
    ):
        self.name = real_name
        self.default = default
        super().__init__(
            cast=cast,
            required=(default is _empty),
        )

    def use(self, **kwargs: Any) -> AnyDict:
        name = self.name or self.param_name

        try:
            kwargs[self.param_name] = resolve_context(name)
        except (KeyError, AttributeError):
            if self.required is False:
                kwargs[self.param_name] = self.default

        return kwargs


def resolve_context(argument: str) -> Any:
    keys = argument.split(".")

    v = context.context[keys[0]]
    for i in keys[1:]:
        v = getattr(v, i)

    return v
