from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Sequence, TypeVar, Union

from pydantic import BaseModel

from faststream._compat import ParamSpec

AnyDict = Dict[str, Any]

F_Return = TypeVar("F_Return")
F_Spec = ParamSpec("F_Spec")

AnyCallable = Callable[..., Any]
NoneCallable = Callable[..., None]
AsyncFunc = Callable[..., Awaitable[Any]]

DecoratedCallable = AnyCallable
DecoratedCallableNone = NoneCallable

JsonDecodable = Union[
    float,
    int,
    bool,
    str,
    bytes,
]
DecodedMessage = Union[Dict[str, JsonDecodable], Sequence[JsonDecodable], JsonDecodable]
SendableMessage = Union[
    datetime,
    DecodedMessage,
    BaseModel,
    None,
]

SettingField = Union[bool, str, List[str]]
