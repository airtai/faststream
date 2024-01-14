from typing import (
    Any,
    AsyncContextManager,
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
from faststream.types import DecodedMessage, SendableMessage

Decoded = TypeVar("Decoded", bound=DecodedMessage)
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
    StreamMsg,
]
AsyncParser: TypeAlias = Callable[
    [MsgType],
    Awaitable[StreamMsg],
]
AsyncCustomParser: TypeAlias = Union[
    AsyncParser[MsgType, StreamMsg],
    Callable[
        [MsgType, AsyncParser[MsgType, StreamMsg]],
        Awaitable[StreamMsg],
    ],
]
Parser: TypeAlias = Union[
    AsyncParser[MsgType, StreamMsg],
    SyncParser[MsgType, StreamMsg],
]
CustomParser: TypeAlias = Union[
    AsyncCustomParser[MsgType, StreamMsg],
    SyncParser[MsgType, StreamMsg],
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
T_HandlerReturn = TypeVar(
    "T_HandlerReturn",
    bound=Union[SendableMessage, Awaitable[SendableMessage]],
    covariant=True,
)


class PublisherProtocol(Protocol):
    """A protocol for an asynchronous publisher."""

    async def publish(
        self,
        message: SendableMessage,
        *args: Any,
        correlation_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        """Publishes a message asynchronously.

        Args:
            message: The message to be published.
            *args: Additional positional arguments.
            correlation_id: Optional correlation ID for the message.
            **kwargs: Additional keyword arguments.

        Returns:
            The response message or None.
        """
        ...


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


BrokerMiddleware: TypeAlias = Callable[[MsgType], BaseMiddleware]
SubscriberMiddleware: TypeAlias = Callable[
    [Optional[DecodedMessage]],
    AsyncContextManager[DecodedMessage],
]
PublisherMiddleware: TypeAlias = Callable[
    [Any],
    AsyncContextManager[SendableMessage],
]
