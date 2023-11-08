from datetime import datetime
from typing import (
    Any,
    AsyncContextManager,
    Awaitable,
    Callable,
    Dict,
    List,
    Sequence,
    TypeVar,
    Union,
)

from pydantic import BaseModel

from faststream._compat import ParamSpec, TypeAlias

AnyDict: TypeAlias = Dict[str, Any]

F_Return = TypeVar("F_Return")
F_Spec = ParamSpec("F_Spec")

AnyCallable: TypeAlias = Callable[..., Any]
NoneCallable: TypeAlias = Callable[..., None]
AsyncFunc: TypeAlias = Callable[..., Awaitable[Any]]

DecoratedCallable: TypeAlias = AnyCallable
DecoratedCallableNone: TypeAlias = NoneCallable

JsonDecodable = Union[
    float,
    int,
    bool,
    str,
    bytes,
]
DecodedMessage: TypeAlias = Union[
    Dict[str, JsonDecodable], Sequence[JsonDecodable], JsonDecodable
]
SendableMessage: TypeAlias = Union[
    datetime,
    DecodedMessage,
    BaseModel,
    None,
]

SettingField: TypeAlias = Union[bool, str, List[str]]

Lifespan: TypeAlias = Callable[..., AsyncContextManager[None]]
