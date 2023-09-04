from typing import Any, Awaitable, Callable, Optional, Protocol, Tuple, TypeVar, Union

from faststream._compat import ParamSpec
from faststream.broker.message import StreamMessage
from faststream.types import DecodedMessage, SendableMessage

Decoded = TypeVar("Decoded", bound=DecodedMessage)
MsgType = TypeVar("MsgType")
ConnectionType = TypeVar("ConnectionType")

SyncFilter = Callable[[MsgType], bool]
AsyncFilter = Callable[[MsgType], Awaitable[bool]]
Filter = Union[SyncFilter[MsgType], AsyncFilter[MsgType]]

SyncParser = Callable[
    [MsgType],
    StreamMessage[MsgType],
]
SyncCustomParser = Union[
    SyncParser[MsgType],
    Callable[
        [MsgType, SyncParser[MsgType]],
        StreamMessage[MsgType],
    ],
]

AsyncParser = Callable[
    [MsgType],
    Awaitable[StreamMessage[MsgType]],
]
AsyncCustomParser = Union[
    AsyncParser[MsgType],
    Callable[
        [MsgType, AsyncParser[MsgType]],
        Awaitable[StreamMessage[MsgType]],
    ],
]

Parser = Union[AsyncParser[MsgType], SyncParser[MsgType]]
CustomParser = Union[AsyncCustomParser[MsgType], SyncCustomParser[MsgType]]

SyncDecoder = Callable[
    [StreamMessage[MsgType]],
    DecodedMessage,
]
SyncCustomDecoder = Union[
    SyncDecoder[MsgType],
    Callable[
        [StreamMessage[MsgType], SyncDecoder[MsgType]],
        DecodedMessage,
    ],
]

AsyncDecoder = Callable[
    [
        StreamMessage[MsgType],
    ],
    Awaitable[DecodedMessage],
]
AsyncCustomDecoder = Union[
    AsyncDecoder[MsgType],
    Callable[
        [StreamMessage[MsgType], AsyncDecoder[MsgType]],
        Awaitable[DecodedMessage],
    ],
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
    [StreamMessage[MsgType]], Awaitable[Optional[WrappedReturn[T_HandlerReturn]]]
]
SyncWrappedHandlerCall = Callable[
    [StreamMessage[MsgType]], Optional[WrappedReturn[T_HandlerReturn]]
]

WrappedHandlerCall = Union[
    AsyncWrappedHandlerCall[MsgType, T_HandlerReturn],
    SyncWrappedHandlerCall[MsgType, T_HandlerReturn],
]
