from collections.abc import Awaitable
from typing import (
    Any,
    Callable,
    Optional,
    Protocol,
    TypeVar,
    Union,
)

from typing_extensions import ParamSpec, TypeAlias

from faststream._internal.basic_types import AsyncFuncAny
from faststream._internal.context.repository import ContextRepo
from faststream.message import StreamMessage
from faststream.middlewares import BaseMiddleware
from faststream.response.response import PublishCommand

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


class BrokerMiddleware(Protocol[MsgType]):
    """Middleware builder interface."""

    def __call__(
        self,
        msg: Optional[MsgType],
        /,
        *,
        context: ContextRepo,
    ) -> BaseMiddleware: ...


SubscriberMiddleware: TypeAlias = Callable[
    [AsyncFuncAny, MsgType],
    MsgType,
]


class PublisherMiddleware(Protocol):
    """Publisher middleware interface."""

    def __call__(
        self,
        call_next: Callable[[PublishCommand], Awaitable[PublishCommand]],
        msg: PublishCommand,
    ) -> Any: ...
