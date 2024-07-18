from .base import BaseMiddleware
from typing import Coroutine, Optional, TypeVar, Callable

E = TypeVar("E", bound=Exception)


class ExceptionMiddleware(BaseMiddleware):
    exc_handlers = dict()

    def __init__(self, exc_handlers: Optional[dict[E, Coroutine]]) -> None:
        if not exc_handlers:
            exc_handlers = dict()
        self._exc_handlers = exc_handlers

    @classmethod
    def add_handler(cls, exc: E) -> Callable:
        def wrapper(func: Coroutine) -> None:
            cls.exc_handlers[exc] = func
        return wrapper

    async def after_consume(self, err: Optional[Exception]) -> None:
        if err:
            handler = self.exc_handlers.get(type(err))
            if handler:
                await handler(err)
            else:
                raise err


add_exception_handler = ExceptionMiddleware.add_handler
