from typing import TYPE_CHECKING, Any, Optional

from typing_extensions import Self

if TYPE_CHECKING:
    from types import TracebackType

    from faststream._internal.basic_types import AsyncFunc, AsyncFuncAny
    from faststream.message import StreamMessage


class BaseMiddleware:
    """A base middleware class."""

    def __init__(self, msg: Optional[Any] = None) -> None:
        self.msg = msg

    async def on_receive(self) -> None:
        """Hook to call on message receive."""

    async def after_processed(
        self,
        exc_type: Optional[type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exc_tb: Optional["TracebackType"] = None,
    ) -> Optional[bool]:
        """Asynchronously called after processing."""
        return False

    async def __aenter__(self) -> Self:
        await self.on_receive()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exc_tb: Optional["TracebackType"] = None,
    ) -> Optional[bool]:
        """Exit the asynchronous context manager."""
        return await self.after_processed(exc_type, exc_val, exc_tb)

    async def on_consume(
        self,
        msg: "StreamMessage[Any]",
    ) -> "StreamMessage[Any]":
        """Asynchronously consumes a message."""
        return msg

    async def after_consume(self, err: Optional[Exception]) -> None:
        """A function to handle the result of consuming a resource asynchronously."""
        if err is not None:
            raise err

    async def consume_scope(
        self,
        call_next: "AsyncFuncAny",
        msg: "StreamMessage[Any]",
    ) -> Any:
        """Asynchronously consumes a message and returns an asynchronous iterator of decoded messages."""
        err: Optional[Exception] = None
        try:
            result = await call_next(await self.on_consume(msg))

        except Exception as e:
            err = e

        else:
            return result

        finally:
            await self.after_consume(err)

    async def on_publish(
        self,
        msg: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Asynchronously handle a publish event."""
        return msg

    async def after_publish(
        self,
        err: Optional[Exception],
    ) -> None:
        """Asynchronous function to handle the after publish event."""
        if err is not None:
            raise err

    async def publish_scope(
        self,
        call_next: "AsyncFunc",
        msg: Any,
    ) -> Any:
        """Publish a message and return an async iterator."""
        err: Optional[Exception] = None
        try:
            result = await call_next(await self.on_publish(msg))

        except Exception as e:
            err = e

        else:
            return result

        finally:
            await self.after_publish(err)
