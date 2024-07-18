from typing import Awaitable, Callable, Optional

from faststream.broker.middlewares.base import BaseMiddleware


class ExceptionMiddleware(BaseMiddleware):

    def __init__(
        self,
        exception_handlers: Optional[
            dict[Exception, Callable[[Exception], Awaitable[None]]]] = None
    ) -> None:
        super().__init__(msg=None)
        if not exception_handlers:
            exception_handlers = {}
        self.exception_handlers = exception_handlers

    async def after_consume(self, err: Optional[Exception]) -> None:
        await self._check_handlers(err)

    async def after_publish(self, err: Optional[Exception]) -> None:
        await self._check_handlers(err)

    async def _check_handlers(self, err: Optional[Exception]):
        if err:
            handler = self.exception_handlers.get(type(err))
            if not handler:
                raise err

            await handler(err)

    def add_handler(self, exc: Exception) -> Callable:

        def wrapper(func: Callable) -> None:
            self.exception_handlers[exc] = func

        return wrapper

    def __call__(self, msg):
        self.msg = msg
        return self
