from typing import Generic, TypeVar

from typing_extensions import Self

T = TypeVar("T")


class Pointer(Generic[T]):
    __slots__ = ("__value",)

    def __init__(self, value: T) -> None:
        self.__value = value

    def change(self, new_value: T) -> "Self":
        self.__value = new_value
        return self

    def get(self) -> T:
        return self.__value
