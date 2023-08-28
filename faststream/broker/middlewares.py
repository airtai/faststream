import logging
from contextlib import asynccontextmanager
from types import TracebackType
from typing import Any, AsyncIterator, Optional, Type

from faststream._compat import Self
from faststream.types import DecodedMessage, SendableMessage


class BaseMiddleware:
    def __init__(self, msg: Any) -> None:
        self.msg = msg

    async def on_receive(self) -> None:
        pass

    async def after_processed(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exec_tb: Optional[TracebackType] = None,
    ) -> Optional[bool]:
        return False

    async def __aenter__(self) -> Self:
        await self.on_receive()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exec_tb: Optional[TracebackType] = None,
    ) -> Optional[bool]:
        return await self.after_processed(exc_type, exc_val, exec_tb)

    async def on_consume(self, msg: DecodedMessage) -> DecodedMessage:
        return msg

    async def after_consume(self, err: Optional[Exception]) -> None:
        if err is not None:
            raise err

    @asynccontextmanager
    async def consume_scope(self, msg: DecodedMessage) -> AsyncIterator[DecodedMessage]:
        err: Optional[Exception]
        try:
            yield await self.on_consume(msg)
        except Exception as e:
            err = e
        else:
            err = None
        await self.after_consume(err)

    async def on_publish(self, msg: SendableMessage) -> SendableMessage:
        return msg

    async def after_publish(self, err: Optional[Exception]) -> None:
        if err is not None:
            raise err

    @asynccontextmanager
    async def publish_scope(
        self, msg: SendableMessage
    ) -> AsyncIterator[SendableMessage]:
        err: Optional[Exception]
        try:
            yield await self.on_publish(msg)
        except Exception as e:
            err = e
        else:
            err = None
        await self.after_publish(err)


class CriticalLogMiddleware(BaseMiddleware):
    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger

    def __call__(self, msg: Any) -> Self:
        return self

    async def after_processed(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exec_tb: Optional[TracebackType] = None,
    ) -> bool:
        if exc_type and exc_val:
            self.logger.critical(f"{exc_type.__name__}: {exc_val}", exc_info=exc_val)
        return True
