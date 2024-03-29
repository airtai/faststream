from abc import abstractmethod
from typing import (
    Any,
    AsyncContextManager,
    Awaitable,
    Callable,
    Iterable,
    Optional,
    Protocol,
    TypeVar,
    Union,
)

from typing_extensions import ParamSpec, TypeAlias

from faststream.broker.message import StreamMessage
from faststream.broker.middlewares import BaseMiddleware
from faststream.types import DecodedMessage, SendableMessage

MsgType = TypeVar("MsgType")
StreamMsg = TypeVar("StreamMsg", bound=StreamMessage[Any])
ConnectionType = TypeVar("ConnectionType")


SyncFilter: TypeAlias = Callable[[StreamMsg], bool]
AsyncFilter: TypeAlias = Callable[[StreamMsg], Awaitable[bool]]
Filter: TypeAlias = Union[
    SyncFilter[StreamMsg],
    AsyncFilter[StreamMsg],
]

SyncParser: TypeAlias = Callable[
    [MsgType],
    StreamMessage[MsgType],
]
AsyncParser: TypeAlias = Callable[
    [MsgType],
    Awaitable[StreamMessage[MsgType]],
]
AsyncCustomParser: TypeAlias = Union[
    AsyncParser[MsgType],
    Callable[
        [MsgType, AsyncParser[MsgType]],
        Awaitable[StreamMessage[MsgType]],
    ],
]
Parser: TypeAlias = Union[
    AsyncParser[MsgType],
    SyncParser[MsgType],
]
CustomParser: TypeAlias = Union[
    AsyncCustomParser[MsgType],
    SyncParser[MsgType],
]

SyncDecoder: TypeAlias = Callable[
    [StreamMsg],
    Any,
]
AsyncDecoder: TypeAlias = Callable[
    [StreamMsg],
    Awaitable[Any],
]
AsyncCustomDecoder: TypeAlias = Union[
    AsyncDecoder[StreamMsg],
    Callable[
        [StreamMsg, AsyncDecoder[StreamMsg]],
        Awaitable[Any],
    ],
]
Decoder: TypeAlias = Union[
    AsyncDecoder[StreamMsg],
    SyncDecoder[StreamMsg],
]
CustomDecoder: TypeAlias = Union[
    AsyncCustomDecoder[StreamMsg],
    SyncDecoder[StreamMsg],
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
    [Optional[DecodedMessage]],
    AsyncContextManager[Optional[DecodedMessage]],
]


class PublisherMiddleware(Protocol):
    """Publisher middleware interface."""

    def __call__(
        self, __msg: Any, /, **__kwargs: Any
    ) -> AsyncContextManager[SendableMessage]:
        ...


class PublisherProtocol(Protocol):
    """A protocol for an asynchronous publisher."""

    @abstractmethod
    async def publish(
        self,
        message: Any,
        /,
        correlation_id: Optional[str] = None,
        extra_middlewares: Iterable[PublisherMiddleware] = (),
    ) -> Optional[Any]:
        """Publishes a message asynchronously."""
        ...
