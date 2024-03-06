from datetime import datetime
from decimal import Decimal
from typing import (
    Any,
    AsyncContextManager,
    Awaitable,
    Callable,
    ClassVar,
    Dict,
    List,
    Protocol,
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

JsonArray: TypeAlias = Sequence["DecodedMessage"]

JsonTable: TypeAlias = Dict[str, "DecodedMessage"]

JsonDecodable: TypeAlias = Union[
    bool,
    bytes,
    bytearray,
    float,
    int,
    str,
    None,
]

DecodedMessage: TypeAlias = Union[
    JsonDecodable,
    JsonArray,
    JsonTable,
]

SendableArray: TypeAlias = Sequence["SendableMessage"]

SendableTable: TypeAlias = Dict[str, "SendableMessage"]

class StandardDataclass(Protocol):
    """Protocol to check type is dataclass."""
    __dataclass_fields__: ClassVar[dict[str, Any]]
    __dataclass_params__: ClassVar[Any]
    __post_init__: ClassVar[Callable[..., None]]

    def __init__(self, *args: object, **kwargs: object) -> None:
        """Interface method."""
        ...

SendableMessage: TypeAlias = Union[
    JsonDecodable,
    Decimal,
    datetime,
    BaseModel,
    None,
    StandardDataclass,
    SendableTable,
    SendableArray,
]

SettingField: TypeAlias = Union[
    bool, str,
    List[Union[bool, str]],
    List[str],
    List[bool],
]

Lifespan: TypeAlias = Callable[..., AsyncContextManager[None]]
