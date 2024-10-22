from enum import Enum
from typing import TYPE_CHECKING, Any, Optional, Type

from .base import BaseMiddleware

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


class AckPolicy(str, Enum):
    ACK = "ack"
    REJECT_ON_ERROR = "reject_on_error"
    NACK_ON_ERROR = "nack_on_error"
    DO_NOTHING = "do_nothing"


class BaseAcknowledgementMiddleware(BaseMiddleware):
    def __init__(
        self,
        ack_policy: AckPolicy,
        msg: Optional[Any] = None,
    ) -> None:
        super().__init__(msg)
        self.ack_policy = ack_policy

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exc_tb: Optional["TracebackType"] = None,
    ) -> Optional[bool]:
        """Exit the asynchronous context manager."""
        if not exc_type:
            print("acked")
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
            if self.ack_policy == AckPolicy.REJECT_ON_ERROR:
                print("rejected")
                await self.__reject()

            elif self.ack_policy == AckPolicy.NACK_ON_ERROR:
                print("nacked")
                await self.__nack()

        # Exception was not processed
        return False

    async def __ack(self, **exc_extra_options: Any) -> None:
        try:
            await self.msg.ack(**exc_extra_options)
        except Exception as er:
            print(er)

    async def __nack(self, **exc_extra_options: Any) -> None:
        try:
            await self.msg.nack(**exc_extra_options)
        except Exception as er:
            print(er)

    async def __reject(self, **exc_extra_options: Any) -> None:
        try:
            await self.msg.reject(**exc_extra_options)
        except Exception as er:
            print(er)


class AcknowledgementMiddleware:
    def __init__(self, ack_policy: AckPolicy):
        self.ack_policy = ack_policy

    def __call__(self, msg: Optional[Any] = None) -> Any:
        return BaseAcknowledgementMiddleware(
            ack_policy=self.ack_policy, msg=msg
        )
