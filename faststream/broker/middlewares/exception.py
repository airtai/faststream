from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

from faststream.broker.middlewares.base import BaseMiddleware

if TYPE_CHECKING:
    from faststream.broker.message import StreamMessage
    from faststream.types import AsyncFuncAny, SendableMessage


class BaseExceptionMiddleware(BaseMiddleware):

    def __init__(
        self,
        exception_handlers: Dict[
            Exception, Callable[[Exception], "SendableMessage"]
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
        try:
            return await call_next(await self.on_consume(msg))

        except Exception as exc:
            if handler := self._exception_handlers.get(type(exc)):
                return await handler(exc)

            raise


class ExceptionMiddleware:
    __slots__ = ("_exception_handlers",)

    def __init__(
        self,
        exception_handlers: Optional[
            Dict[Exception, Callable[[Exception], "SendableMessage"]]
        ] = None
    ) -> None:
        if not exception_handlers:
            exception_handlers = {}
        self._exception_handlers = exception_handlers

    def add_handler(
        self, exc: Exception
    ) -> Callable[[Callable[[Exception], "SendableMessage"]], None]:
        def wrapper(func: Callable[[Exception], "SendableMessage"]) -> None:
            self._exception_handlers[exc] = func

        return wrapper

    def __call__(self, msg: Optional[Any]) -> BaseMiddleware:
        return BaseExceptionMiddleware(
            exception_handlers=self._exception_handlers, msg=msg
        )
