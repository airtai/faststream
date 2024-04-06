from typing import TYPE_CHECKING, List, Union

from faststream.broker.message import StreamMessage

if TYPE_CHECKING:
    from nats.aio.msg import Msg


class NatsMessage(StreamMessage["Msg"]):
    """A class to represent a NATS message."""

    async def ack(self) -> None:
        # Check `self.raw_message._ackd` instead of `self.committed`
        # to be compatible with `self.raw_message.ack()`
        if not self.raw_message._ackd:
            await self.raw_message.ack()
            await super().ack()

    async def nack(
        self,
        delay: Union[int, float, None] = None,
    ) -> None:
        if not self.raw_message._ackd:
            await self.raw_message.nak(delay=delay)
            await super().nack()

    async def reject(self) -> None:
        if not self.raw_message._ackd:
            await self.raw_message.term()
            await super().reject()

    async def in_progress(self) -> None:
        if not self.raw_message._ackd:
            await self.raw_message.in_progress()


class NatsBatchMessage(StreamMessage[List["Msg"]]):
    """A class to represent a NATS batch message."""

    async def ack(self) -> None:
        for m in filter(
            lambda m: not m._ackd,
            self.raw_message,
        ):
            await m.ack()

        await super().ack()

    async def nack(
        self,
        delay: Union[int, float, None] = None,
    ) -> None:
        for m in filter(
            lambda m: not m._ackd,
            self.raw_message,
        ):
            await m.nak(delay=delay)

        await super().nack()

    async def reject(self) -> None:
        for m in filter(
            lambda m: not m._ackd,
            self.raw_message,
        ):
            await m.term()

        await super().reject()

    async def in_progress(self) -> None:
        for m in filter(
            lambda m: not m._ackd,
            self.raw_message,
        ):
            await m.in_progress()
