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
    Mapping,
    Optional,
    Protocol,
    Sequence,
    TypeVar,
    Union,
)

from typing_extensions import ParamSpec, TypeAlias

# Type Aliases
AnyDict: TypeAlias = Dict[str, Any]
AnyHttpUrl: TypeAlias = str

F_Return = TypeVar("F_Return")
F_Spec = ParamSpec("F_Spec")

AnyCallable: TypeAlias = Callable[..., Any]
NoneCallable: TypeAlias = Callable[..., None]
AsyncFunc: TypeAlias = Callable[..., Awaitable[Any]]
AsyncFuncAny: TypeAlias = Callable[[Any], Awaitable[Any]]

DecoratedCallable: TypeAlias = AnyCallable
DecoratedCallableNone: TypeAlias = NoneCallable

Decorator: TypeAlias = Callable[[AnyCallable], AnyCallable]

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

SendableArray: TypeAlias = Sequence["BaseSendableMessage"]
SendableTable: TypeAlias = Dict[str, "BaseSendableMessage"]

# Protocol for Dataclasses
class StandardDataclass(Protocol):
    """Protocol to check type is dataclass."""

    __dataclass_fields__: ClassVar[Dict[str, Any]]


BaseSendableMessage: TypeAlias = Union[
    JsonDecodable,
    Decimal,
    datetime,
    StandardDataclass,
    SendableTable,
    SendableArray,
    None,
]

# Handling ImportError for BaseModel
try:
    from faststream._compat import BaseModel

    SendableMessage: TypeAlias = Union[
        BaseModel,
        BaseSendableMessage,
    ]

except ImportError:
    SendableMessage: TypeAlias = BaseSendableMessage  # type: ignore[no-redef,misc]

# Type alias for configuration settings
SettingField: TypeAlias = Union[
    bool,
    str,
    List[Union[bool, str]],
    List[str],
    List[bool],
]

# Alias for a callable context manager used for lifespan
Lifespan: TypeAlias = Callable[..., AsyncContextManager[None]]


# Protocol for Logger with type hints
class LoggerProto(Protocol):
    def log(
        self,
        level: int,
        msg: Any,
        /,
        *,
        exc_info: Any = None,
        extra: Optional[Mapping[str, Any]] = None,
    ) -> None: ...


# Placeholder class with type hints
class _EmptyPlaceholder:
    def __repr__(self) -> str:
        return "EMPTY"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _EmptyPlaceholder)


EMPTY: Any = _EmptyPlaceholder()
