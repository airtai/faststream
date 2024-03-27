import asyncio
from typing import Any, Awaitable, Callable, Generic, List, Optional, Union
from unittest.mock import MagicMock

import anyio

from faststream.broker.message import StreamMessage
from faststream.broker.types import (
    MsgType,
    P_HandlerParams,
    PublisherProtocol,
    T_HandlerReturn,
)
from faststream.exceptions import SetupError


class HandlerCallWrapper(Generic[MsgType, P_HandlerParams, T_HandlerReturn]):
    """A generic class to wrap handler calls.

    Attributes:
        mock : MagicMock object used for mocking

        _wrapped_call : WrappedHandlerCall object representing the wrapped handler call
        _original_call : original handler call
        _publishers : list of PublisherProtocol objects

    Methods:
        __new__ : Create a new instance of the class
        __init__ : Initialize the instance
        __call__ : Call the wrapped handler
        set_wrapped : Set the wrapped handler call
        call_wrapped : Call the wrapped handler
        wait_call : Wait for the handler call to complete
    """

    mock: Optional[MagicMock]
    future: Optional["asyncio.Future[Any]"]
    is_test: bool

    _wrapped_call: Optional[Callable[..., Awaitable[Any]]]
    _original_call: Callable[P_HandlerParams, T_HandlerReturn]
    _publishers: List[PublisherProtocol]

    __slots__ = (
        "mock",
        "future",
        "is_test",
        "_wrapped_call",
        "_original_call",
        "_publishers",
    )

    def __new__(
        cls,
        call: Union[
            "HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]",
            Callable[P_HandlerParams, T_HandlerReturn],
        ],
    ) -> "HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]":
        """Create a new instance of the class.

        Args:
            call: An instance of "HandlerCallWrapper" or a callable object

        Returns:
            An instance of the class

        Note:
            If the "call" argument is already an instance of the class, it is returned as is. Otherwise, a new instance of the class is created using the superclass's __new__ method.
        """
        if isinstance(call, cls):
            return call
        else:
            return super().__new__(cls)

    def __init__(
        self,
        call: Callable[P_HandlerParams, T_HandlerReturn],
    ) -> None:
        """Initialize a handler.

        Args:
            call: A callable object that represents the handler function.

        Attributes:
            _original_call: The original handler function.
            _wrapped_call: The wrapped handler function.
            _publishers: A list of publishers.
            mock: A MagicMock object.
        """
        if not isinstance(call, HandlerCallWrapper):
            self._original_call = call
            self._wrapped_call = None
            self._publishers = []

            self.mock = None
            self.future = None
            self.is_test = False

    def __call__(
        self,
        *args: P_HandlerParams.args,
        **kwargs: P_HandlerParams.kwargs,
    ) -> T_HandlerReturn:
        """Calls the object as a function.

        Args:
            *args: Positional arguments to be passed to the function.
            **kwargs: Keyword arguments to be passed to the function.

        Returns:
            The return value of the function.

        """
        return self._original_call(*args, **kwargs)

    def set_wrapped(self, wrapped: Callable[..., Awaitable[Any]]) -> None:
        """Set the wrapped handler call.

        Args:
            wrapped: The wrapped handler call to set

        """
        self._wrapped_call = wrapped

    def call_wrapped(
        self,
        message: StreamMessage[MsgType],
    ) -> Awaitable[Any]:
        """Calls the wrapped function with the given message.

        Args:
            message: The message to be passed to the wrapped function.

        Returns:
            The result of the wrapped function call.
        """
        assert self._wrapped_call, "You should use `set_wrapped` first"  # nosec B101
        if self.is_test:
            assert self.mock  # nosec B101
            self.mock(message.decoded_body)
        return self._wrapped_call(message)

    async def wait_call(self, timeout: Optional[float] = None) -> None:
        """Waits for a call with an optional timeout.

        Args:
            timeout: Optional timeout in seconds

        Raises:
            AssertionError: If the broker is not started

        Returns:
            None
        """
        assert (  # nosec B101
            self.future is not None
        ), "You can use this method only with TestClient"
        with anyio.fail_after(timeout):
            await self.future

    def set_test(self) -> None:
        self.is_test = True
        if self.mock is None:
            self.mock = MagicMock()
        self.refresh(with_mock=True)

    def reset_test(self) -> None:
        self.is_test = False
        self.mock = None
        self.future = None

    def trigger(
        self,
        result: Any = None,
        error: Optional[BaseException] = None,
    ) -> None:
        if not self.is_test:
            return

        if self.future is None:
            raise SetupError("You can use this method only with TestClient")

        if self.future.done():
            self.future = asyncio.Future()

        if error:
            self.future.set_exception(error)
        else:
            self.future.set_result(result)

    def refresh(self, with_mock: bool = False) -> None:
        self.future = asyncio.Future()
        if with_mock and self.mock is not None:
            self.mock.reset_mock()
