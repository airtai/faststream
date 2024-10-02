from abc import abstractmethod
from typing import Any, Optional, Protocol, TypeVar, Union, overload

from .setup import SetupAble


class Endpoint(SetupAble, Protocol):
    @abstractmethod
    def add_prefix(self, prefix: str) -> None: ...


NameRequiredCls = TypeVar("NameRequiredCls", bound="NameRequired")


class NameRequired:
    """Required name option object."""

    def __eq__(self, value: object, /) -> bool:
        """Compares the current object with another object for equality."""
        if value is None:
            return False

        if not isinstance(value, NameRequired):
            return NotImplemented

        return self.name == value.name

    def __init__(self, name: str) -> None:
        self.name = name

    @overload
    @classmethod
    def validate(
        cls: type[NameRequiredCls],
        value: Union[str, NameRequiredCls],
        **kwargs: Any,
    ) -> NameRequiredCls: ...

    @overload
    @classmethod
    def validate(
        cls: type[NameRequiredCls],
        value: None,
        **kwargs: Any,
    ) -> None: ...

    @classmethod
    def validate(
        cls: type[NameRequiredCls],
        value: Union[str, NameRequiredCls, None],
        **kwargs: Any,
    ) -> Optional[NameRequiredCls]:
        """Factory to create object."""
        if value is not None and isinstance(value, str):
            value = cls(value, **kwargs)
        return value
