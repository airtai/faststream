from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Type

from faststream.broker.middlewares.base import BaseMiddleware

if TYPE_CHECKING:
    from faststream.broker.message import StreamMessage
    from faststream.types import AsyncFuncAny, SendableMessage


class BaseExceptionMiddleware(BaseMiddleware):

    def __init__(
        self,
        handlers: Dict[
            Exception, Callable[[Exception, StreamMessage], None]
        ],
        publish_handlers: Dict[
            Exception, Callable[[Exception], "SendableMessage"]
        ],
        msg: Optional[Any] = None,
    ) -> None:
        super().__init__(msg)
        self._handlers = handlers
        self._publish_handlers = publish_handlers

    async def consume_scope(
        self,
        call_next: "AsyncFuncAny",
        msg: "StreamMessage[Any]",
    ) -> Any:
        try:
            return await call_next(await self.on_consume(msg))

        except Exception as exc:
            if handler := self._publish_handlers.get(type(exc)):
                return await handler(exc)

            raise

    async def after_processed(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exc_tb: Optional["TracebackType"] = None,
    ) -> Optional[bool]:
        for handler_type in self._handlers.keys():
            if issubclass(exc_type, handler_type):
                if handler := self._handlers.get(handler_type):
                    await handler(exc_val, self.msg)
                    return True

        return False


class ExceptionMiddleware:
    __slots__ = ("_handlers", "_publish_handlers")

    def __init__(
        self,
        handlers: Optional[
            Dict[Exception, Callable[[Exception, StreamMessage], None]]
        ] = None,
        publish_handlers: Optional[
            Dict[Exception, Callable[[Exception], "SendableMessage"]]
        ] = None
    ) -> None:
        self._handlers = handlers if handlers else {}
        self._publish_handlers = publish_handlers if publish_handlers else {}

    def add_handler(
        self, exc: Exception, publish: bool = False
    ) -> Callable[
        [Callable[[Exception], Optional["SendableMessage"]]],
        Callable[[Exception], Optional["SendableMessage"]]
    ]:
        def wrapper(
            func: Callable[[Exception], Optional["SendableMessage"]]
        ) -> Callable[[Exception], Optional["SendableMessage"]]:
            if publish:
                self._publish_handlers[exc] = func
            else:
                self._handlers[exc] = func

            return func

        return wrapper

    def __call__(self, msg: Optional[Any]) -> BaseMiddleware:
        return BaseExceptionMiddleware(
            handlers=self._handlers,
            publish_handlers=self._publish_handlers,
            msg=msg,
        )
