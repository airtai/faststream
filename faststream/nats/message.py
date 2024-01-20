from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, List

from faststream.broker.message import StreamMessage

if TYPE_CHECKING:
    from nats.aio.msg import Msg


@dataclass
class NatsMessage(StreamMessage["Msg"]):
    """A class to represent a NATS message."""

    is_js: bool = True

    async def ack(self, **kwargs: Any) -> None:
        await super().ack()
        if self.is_js and not self.raw_message._ackd:
            await self.raw_message.ack()

    async def nack(self, **kwargs: Any) -> None:
        await super().nack()
        if self.is_js and not self.raw_message._ackd:
            await self.raw_message.nak(**kwargs)

    async def reject(self, **kwargs: Any) -> None:
        await super().reject()
        if self.is_js and not self.raw_message._ackd:
            await self.raw_message.term()

    async def in_progress(self, **kwargs: Any) -> None:
        if self.is_js and not self.raw_message._ackd:
            await self.raw_message.in_progress()


@dataclass
class NatsBatchMessage(StreamMessage[List["Msg"]]):
    """A class to represent a NATS batch message."""

    is_js: bool = True

    async def ack(self, **kwargs: Any) -> None:
        await super().ack()
        if self.is_js:
            for m in filter(
                lambda m: not m._ackd,
                self.raw_message,
            ):
                await m.ack()

    async def nack(self, **kwargs: Any) -> None:
        await super().nack()
        if self.is_js:
            for m in filter(
                lambda m: not m._ackd,
                self.raw_message,
            ):
                await m.nak(**kwargs)

    async def reject(self, **kwargs: Any) -> None:
        await super().reject()
        if self.is_js:
            for m in filter(
                lambda m: not m._ackd,
                self.raw_message,
            ):
                await m.term()

    async def in_progress(self, **kwargs: Any) -> None:
        if self.is_js:
            for m in filter(
                lambda m: not m._ackd,
                self.raw_message,
            ):
                await m.in_progress()
