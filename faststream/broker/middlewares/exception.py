from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict, Optional

from faststream.broker.middlewares.base import BaseMiddleware

if TYPE_CHECKING:
    from faststream.broker.message import StreamMessage
    from faststream.types import AsyncFuncAny


class BaseExceptionMiddleware(BaseMiddleware):

    def __init__(
        self,
        exception_handlers: Dict[
            Exception, Callable[[Exception], Awaitable[None]]
        ],
        msg: Optional[Any] = None,
    ) -> None:
        super().__init__(msg)
        self._exception_handlers = exception_handlers

    async def consume_scope(
        self,
        call_next: "AsyncFuncAny",
        msg: "StreamMessage[Any]",
    ) -> Any:
        err: Optional[Exception] = None
        try:
            result = await call_next(await self.on_consume(msg))

        except Exception as exc:
            handler = self._exception_handlers.get(type(exc))
            if handler:
                await handler(exc)
            else:
                err = exc

        else:
            return result

        finally:
            await self.after_consume(err)


class ExceptionMiddleware:
    __slots__ = ("_exception_handlers",)

    def __init__(
        self,
        exception_handlers: Optional[
            Dict[Exception, Callable[[Exception], Awaitable[None]]]
        ] = None
    ) -> None:
        if not exception_handlers:
            exception_handlers = {}
        self._exception_handlers = exception_handlers

    def add_handler(self, exc: Exception) -> Callable:
        def wrapper(func: Callable) -> None:
            self._exception_handlers[exc] = func

        return wrapper

    def __call__(self, msg: Optional[Any]) -> BaseMiddleware:
        return BaseExceptionMiddleware(
            exception_handlers=self._exception_handlers, msg=msg
        )
