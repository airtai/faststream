import asyncio
from typing import Any, Awaitable, Callable, Generic, List, Optional, Protocol, Union
from unittest.mock import MagicMock

import anyio

from propan._compat import Self
from propan.broker.message import PropanMessage
from propan.broker.types import (
    MsgType,
    P_HandlerParams,
    T_HandlerReturn,
    WrappedHandlerCall,
)
from propan.types import SendableMessage


class AsyncPublisherProtocol(Protocol):
    async def publish(
        self,
        message: SendableMessage,
        correlation_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Optional[SendableMessage]:
        ...


class HandlerCallWrapper(Generic[MsgType, P_HandlerParams, T_HandlerReturn]):
    mock: MagicMock
    event: asyncio.Event

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
            self.event = asyncio.Event()
            self.__name__ = getattr(self._original_call, "__name__", "undefined")

    def __call__(
        self,
        *args: P_HandlerParams.args,
        **kwargs: P_HandlerParams.kwargs,
    ) -> T_HandlerReturn:
        self.mock(*args, **kwargs)
        self.event.set()
        return self._original_call(*args, **kwargs)

    def set_wrapped(
        self, wrapped: WrappedHandlerCall[MsgType, T_HandlerReturn]
    ) -> None:
        self._wrapped_call = wrapped

    def call_wrapped(
        self,
        message: PropanMessage[MsgType],
        reraise_exc: bool = False,
    ) -> Union[Optional[T_HandlerReturn], Awaitable[Optional[T_HandlerReturn]]]:
        assert self._wrapped_call, "You should use `set_wrapped` first"
        self.mock(message.decoded_body)
        self.event.set()
        return self._wrapped_call(message, reraise_exc=reraise_exc)

    async def wait_call(self, timeout: Optional[float] = None) -> None:
        with anyio.fail_after(timeout):
            await self.event.wait()
