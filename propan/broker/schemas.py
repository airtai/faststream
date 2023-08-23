from typing import Any, Optional, Type, TypeVar, Union, overload

from pydantic import BaseModel, Field, Json

Cls = TypeVar("Cls")
NameRequiredCls = TypeVar("NameRequiredCls", bound="NameRequired")


class NameRequired(BaseModel):
    name: Optional[str] = Field(...)

    def __eq__(self, __value: object) -> bool:
        if __value is None:
            return False

        if not isinstance(__value, NameRequired):  # pragma: no cover
            return NotImplemented

        return self.name == __value.name

    def __init__(self, name: str, **kwargs: Any):
        super().__init__(name=name, **kwargs)

    @overload
    @classmethod
    def validate(
        cls: Type[NameRequiredCls], value: Union[str, NameRequiredCls]
    ) -> NameRequiredCls:
        ...

    @overload
    @classmethod
    def validate(cls: Type[NameRequiredCls], value: None) -> None:
        ...

    @classmethod
    def validate(
        cls: Type[NameRequiredCls], value: Union[str, NameRequiredCls, None]
    ) -> Optional[NameRequiredCls]:
        if value is not None:
            if isinstance(value, str):
                value = cls(value)
        return value


class RawDecoced(BaseModel):
    message: Union[Json[Any], str]
