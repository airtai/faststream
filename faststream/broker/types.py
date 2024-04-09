from typing import (
    Any,
    Awaitable,
    Callable,
    Optional,
    Protocol,
    TypeVar,
    Union,
)

from typing_extensions import ParamSpec, TypeAlias

from faststream.broker.message import StreamMessage
from faststream.broker.middlewares import BaseMiddleware
from faststream.types import AsyncFunc, AsyncFuncAny

MsgType = TypeVar("MsgType")
StreamMsg = TypeVar("StreamMsg", bound=StreamMessage[Any])
ConnectionType = TypeVar("ConnectionType")


SyncFilter: TypeAlias = Callable[[StreamMsg], bool]
AsyncFilter: TypeAlias = Callable[[StreamMsg], Awaitable[bool]]
Filter: TypeAlias = Union[
    SyncFilter[StreamMsg],
    AsyncFilter[StreamMsg],
]

SyncCallable: TypeAlias = Callable[
    [Any],
    Any,
]
AsyncCallable: TypeAlias = Callable[
    [Any],
    Awaitable[Any],
]
AsyncCustomCallable: TypeAlias = Union[
    AsyncCallable,
    Callable[
        [Any, AsyncCallable],
        Awaitable[Any],
    ],
]
CustomCallable: TypeAlias = Union[
    AsyncCustomCallable,
    SyncCallable,
]

P_HandlerParams = ParamSpec("P_HandlerParams")
T_HandlerReturn = TypeVar("T_HandlerReturn")


AsyncWrappedHandlerCall: TypeAlias = Callable[
    [StreamMessage[MsgType]],
    Awaitable[Optional[T_HandlerReturn]],
]
SyncWrappedHandlerCall: TypeAlias = Callable[
    [StreamMessage[MsgType]],
    Optional[T_HandlerReturn],
]
WrappedHandlerCall: TypeAlias = Union[
    AsyncWrappedHandlerCall[MsgType, T_HandlerReturn],
    SyncWrappedHandlerCall[MsgType, T_HandlerReturn],
]


BrokerMiddleware: TypeAlias = Callable[[Optional[MsgType]], BaseMiddleware]
SubscriberMiddleware: TypeAlias = Callable[
    [AsyncFuncAny, MsgType],
    MsgType,
]


class PublisherMiddleware(Protocol):
    """Publisher middleware interface."""

    def __call__(
        self,
        call_next: AsyncFunc,
        *__args: Any,
        **__kwargs: Any,
    ) -> Any: ...
