from typing import TYPE_CHECKING, Any, Optional, Type
import logging

from faststream.middlewares.base import BaseMiddleware
from faststream.middlewares.acknowledgement.conf import AckPolicy
from faststream._internal.setup.logger import LoggerState

if TYPE_CHECKING:
    from types import TracebackType

from faststream.exceptions import (
    AckMessage,
    HandlerException,
    NackMessage,
    RejectMessage,
)

if TYPE_CHECKING:
    from types import TracebackType


class BaseAcknowledgementMiddleware(BaseMiddleware):
    def __init__(
        self,
        ack_policy: AckPolicy,
        logger: LoggerState,
        msg: Optional[Any] = None,
    ) -> None:
        super().__init__(msg)
        self.ack_policy = ack_policy
        self.logger = logger

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exc_tb: Optional["TracebackType"] = None,
    ) -> Optional[bool]:
        """Exit the asynchronous context manager."""
        if self.ack_policy is AckPolicy.DO_NOTHING:
            return False

        if not exc_type:
            await self.__ack()

        elif isinstance(exc_val, HandlerException):
            if isinstance(exc_val, AckMessage):
                await self.__ack(**exc_val.extra_options)

            elif isinstance(exc_val, NackMessage):
                await self.__nack(**exc_val.extra_options)

            elif isinstance(exc_val, RejectMessage):  # pragma: no branch
                await self.__reject(**exc_val.extra_options)

            # Exception was processed and suppressed
            return True

        else:
            if self.ack_policy is AckPolicy.REJECT_ON_ERROR:
                await self.__reject()

            elif self.ack_policy is AckPolicy.NACK_ON_ERROR:
                await self.__nack()

        # Exception was not processed
        return False

    async def __ack(self, **exc_extra_options: Any) -> None:
        try:
            await self.msg.ack(**exc_extra_options)
        except Exception as er:
            if self.logger is not None:
                self.logger.log(logging.ERROR, er, exc_info=er)

    async def __nack(self, **exc_extra_options: Any) -> None:
        try:
            await self.msg.nack(**exc_extra_options)
        except Exception as er:
            if self.logger is not None:
                self.logger.log(logging.ERROR, er, exc_info=er)

    async def __reject(self, **exc_extra_options: Any) -> None:
        try:
            await self.msg.reject(**exc_extra_options)
        except Exception as er:
            if self.logger is not None:
                self.logger.log(logging.ERROR, er, exc_info=er)


class AcknowledgementMiddleware:
    def __init__(self, ack_policy: AckPolicy, logger: LoggerState):
        self.ack_policy = ack_policy
        self.logger = logger

    def __call__(self, msg: Optional[Any] = None) -> Any:
        return BaseAcknowledgementMiddleware(
            ack_policy=self.ack_policy, logger=self.logger, msg=msg
        )
