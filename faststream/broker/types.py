from typing import Any, Awaitable, Callable, Optional, Protocol, Tuple, TypeVar, Union

from typing_extensions import ParamSpec, TypeAlias

from faststream.broker.message import StreamMessage
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


class AsyncPublisherProtocol(Protocol):
    """A protocol for an asynchronous publisher."""

    async def publish(
        self,
        message: SendableMessage,
        correlation_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Optional[SendableMessage]:
        """Publishes a message asynchronously.

        Args:
            message: The message to be published.
            correlation_id: Optional correlation ID for the message.
            **kwargs: Additional keyword arguments.

        Returns:
            The published message, or None if the message was not published.

        """
        ...


WrappedReturn: TypeAlias = Tuple[T_HandlerReturn, Optional[AsyncPublisherProtocol]]

AsyncWrappedHandlerCall: TypeAlias = Callable[
    [StreamMessage[MsgType]],
    Awaitable[Optional[WrappedReturn[T_HandlerReturn]]],
]
SyncWrappedHandlerCall: TypeAlias = Callable[
    [StreamMessage[MsgType]],
    Optional[WrappedReturn[T_HandlerReturn]],
]
WrappedHandlerCall: TypeAlias = Union[
    AsyncWrappedHandlerCall[MsgType, T_HandlerReturn],
    SyncWrappedHandlerCall[MsgType, T_HandlerReturn],
]
