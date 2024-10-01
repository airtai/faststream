from abc import abstractmethod
from typing import (
    Any,
    Optional,
    Protocol,
    Type,
    TypeVar,
    Union,
    overload,
    runtime_checkable,
)

from .setup import SetupAble


class Endpoint(SetupAble, Protocol):
    @abstractmethod
    def add_prefix(self, prefix: str) -> None: ...


NameRequiredCls = TypeVar("NameRequiredCls", bound="NameRequired")


class NameRequired:
    """Required name option object."""

    def __eq__(self, __value: object) -> bool:
        """Compares the current object with another object for equality."""
        if __value is None:
            return False

        if not isinstance(__value, NameRequired):
            return NotImplemented

        return self.name == __value.name

    def __init__(self, name: str) -> None:
        self.name = name

    @overload
    @classmethod
    def validate(
        cls: Type[NameRequiredCls],
        value: Union[str, NameRequiredCls],
        **kwargs: Any,
    ) -> NameRequiredCls: ...

    @overload
    @classmethod
    def validate(
        cls: Type[NameRequiredCls],
        value: None,
        **kwargs: Any,
    ) -> None: ...

    @classmethod
    def validate(
        cls: Type[NameRequiredCls],
        value: Union[str, NameRequiredCls, None],
        **kwargs: Any,
    ) -> Optional[NameRequiredCls]:
        """Factory to create object."""
        if value is not None and isinstance(value, str):
            value = cls(value, **kwargs)
        return value


@runtime_checkable
class NamedEntity(Protocol):
    def __init__(self, name: Optional[str]) -> None:
        raise NotImplementedError

    @property
    def name(self) -> str:
        raise NotImplementedError


class SimpleName(NamedEntity):
    def __init__(self, name: Optional[str]) -> None:
        self.__name = name or ""

    @property
    def name(self) -> str:
        return self.__name


class NameProxy(NamedEntity):
    _prefix: "NamedEntity"
    _value: Union[str, "NamedEntity", None]

    def __init__(
        self,
        name: Optional[str] = None,
    ) -> None:
        self._prefix = SimpleName("")
        self._value = SimpleName(name) if name else None

    def add_prefix(self, prefix: str) -> "NamedEntity":
        obj = type(self)(None)
        obj._value = self
        obj._prefix = SimpleName(prefix)
        return obj

    @property
    def name(self) -> str:
        if self._value is None:
            raise ValueError

        if isinstance(self._value, NamedEntity):
            return f"{self._prefix.name}{self._value.name}"

        else:
            return f"{self._prefix.name}{self._value}"

    @name.setter
    def name(self, value: str) -> None:
        self._value = value

    @classmethod
    def validate(
        cls,
        name: Union[str, None, "NamedEntity"] = None,
    ) -> "NamedEntity":
        if name and isinstance(name, NamedEntity):
            return name
        return cls(name)
