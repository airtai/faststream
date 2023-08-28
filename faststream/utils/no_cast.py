from typing import Any

from fast_depends.library import CustomField

from faststream.types import AnyDict


class NoCast(CustomField):
    def __init__(self) -> None:
        super().__init__(cast=False)

    def use(self, **kwargs: Any) -> AnyDict:
        return kwargs
