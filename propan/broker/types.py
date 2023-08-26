from typing import Any, Awaitable, Callable, Optional, Protocol, Tuple, TypeVar, Union

from propan._compat import ParamSpec
from propan.broker.message import PropanMessage
from propan.types import DecodedMessage, SendableMessage

Decoded = TypeVar("Decoded", bound=DecodedMessage)
MsgType = TypeVar("MsgType")
ConnectionType = TypeVar("ConnectionType")

SyncParser = Callable[
    [MsgType],
    PropanMessage[MsgType],
]
AsyncParser = Callable[
    [MsgType],
    Awaitable[PropanMessage[MsgType]],
]
SyncCustomParser = Callable[
    [MsgType, SyncParser[MsgType]],
    PropanMessage[MsgType],
]
AsyncCustomParser = Callable[
    [MsgType, SyncParser[MsgType]],
    Awaitable[PropanMessage[MsgType]],
]
Parser = Union[AsyncParser[MsgType], SyncParser[MsgType]]
CustomParser = Union[AsyncCustomParser[MsgType], SyncCustomParser[MsgType]]

SyncDecoder = Callable[
    [PropanMessage[MsgType]],
    DecodedMessage,
]
SyncCustomDecoder = Callable[
    [PropanMessage[MsgType], SyncDecoder[MsgType]],
    DecodedMessage,
]
AsyncDecoder = Callable[
    [
        PropanMessage[MsgType],
    ],
    Awaitable[DecodedMessage],
]
AsyncCustomDecoder = Callable[
    [PropanMessage[MsgType], AsyncDecoder[MsgType]],
    Awaitable[DecodedMessage],
]
Decoder = Union[AsyncDecoder[MsgType], SyncDecoder[MsgType]]
CustomDecoder = Union[AsyncCustomDecoder[MsgType], SyncCustomDecoder[MsgType]]

P_HandlerParams = ParamSpec("P_HandlerParams")
T_HandlerReturn = TypeVar("T_HandlerReturn", bound=SendableMessage, covariant=True)

HandlerCallable = Callable[..., Union[T_HandlerReturn, Awaitable[T_HandlerReturn]]]

HandlerWrapper = Callable[
    [HandlerCallable[T_HandlerReturn]],
    HandlerCallable[T_HandlerReturn],
]


class AsyncPublisherProtocol(Protocol):
    async def publish(
        self,
        message: SendableMessage,
        correlation_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Optional[SendableMessage]:
        ...


WrappedReturn = Tuple[T_HandlerReturn, Optional[AsyncPublisherProtocol]]

AsyncWrappedHandlerCall = Callable[
    [PropanMessage[MsgType]], Awaitable[Optional[WrappedReturn[T_HandlerReturn]]]
]
SyncWrappedHandlerCall = Callable[
    [PropanMessage[MsgType]], Optional[WrappedReturn[T_HandlerReturn]]
]

WrappedHandlerCall = Union[
    AsyncWrappedHandlerCall[MsgType, T_HandlerReturn],
    SyncWrappedHandlerCall[MsgType, T_HandlerReturn],
]
