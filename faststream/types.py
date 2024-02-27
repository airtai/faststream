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
from typing_extensions import ParamSpec, TypeAlias

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
    Dict[str, JsonDecodable],
    Sequence[JsonDecodable],
    JsonDecodable,
]
JsonCompatible: TypeAlias = Union[JsonDecodable, datetime]
SendableMessage: TypeAlias = Union[
    Dict[str, Union[JsonCompatible, Sequence[JsonCompatible]]],
    Sequence[JsonCompatible],
    JsonCompatible,
    BaseModel,
    None,
]

SettingField: TypeAlias = Union[
    bool, str, List[Union[bool, str]], List[str], List[bool]
]

Lifespan: TypeAlias = Callable[..., AsyncContextManager[None]]
