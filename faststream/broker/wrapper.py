from typing import Any, Awaitable, Callable, Generic, List, Optional, Union
from unittest.mock import MagicMock

import anyio

from faststream._compat import Self
from faststream.broker.message import StreamMessage
from faststream.broker.types import (
    AsyncPublisherProtocol,
    MsgType,
    P_HandlerParams,
    T_HandlerReturn,
    WrappedHandlerCall,
    WrappedReturn,
)
from faststream.types import SendableMessage


class FakePublisher:
    def __init__(self, method: Callable[..., Awaitable[SendableMessage]]):
        self.method = method

    async def publish(
        self,
        message: SendableMessage,
        correlation_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Optional[SendableMessage]:
        return await self.method(message, correlation_id=correlation_id, **kwargs)


class HandlerCallWrapper(Generic[MsgType, P_HandlerParams, T_HandlerReturn]):
    mock: MagicMock
    event: Optional[anyio.Event]

    _wrapped_call: Optional[WrappedHandlerCall[MsgType, T_HandlerReturn]]
    _original_call: Callable[P_HandlerParams, T_HandlerReturn]
    _publishers: List[AsyncPublisherProtocol]

    def __new__(
        cls,
        call: Union[
            "HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]",
            Callable[P_HandlerParams, T_HandlerReturn],
        ],
    ) -> Self:
        if isinstance(call, cls):
            return call
        else:
            return super().__new__(cls)

    def __init__(
        self,
        call: Callable[P_HandlerParams, T_HandlerReturn],
    ):
        if not isinstance(call, HandlerCallWrapper):
            self._original_call = call
            self._wrapped_call = None
            self._publishers = []
            self.mock = MagicMock()
            self.event = None
            self.__name__ = getattr(self._original_call, "__name__", "undefined")

    def __call__(
        self,
        *args: P_HandlerParams.args,
        **kwargs: P_HandlerParams.kwargs,
    ) -> T_HandlerReturn:
        self.mock(*args, **kwargs)
        if self.event is not None:
            self.event.set()
        return self._original_call(*args, **kwargs)

    def set_wrapped(
        self, wrapped: WrappedHandlerCall[MsgType, T_HandlerReturn]
    ) -> None:
        self._wrapped_call = wrapped

    def call_wrapped(
        self,
        message: StreamMessage[MsgType],
    ) -> Union[
        Optional[WrappedReturn[T_HandlerReturn]],
        Awaitable[Optional[WrappedReturn[T_HandlerReturn]]],
    ]:
        if self._wrapped_call is None:
            raise RuntimeError("You should use `set_wrapped` first")
        if self.event is None:
            raise RuntimeError("You should start the broker first")
        self.mock(message.decoded_body)
        self.event.set()
        return self._wrapped_call(message)

    async def wait_call(self, timeout: Optional[float] = None) -> None:
        if self.event is None:
            raise RuntimeError("You should start the broker first")
        with anyio.fail_after(timeout):
            await self.event.wait()
