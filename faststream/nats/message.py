from typing import Optional

from nats.aio.msg import Msg
from nats.js.api import ObjectInfo
from nats.js.kv import KeyValue

from faststream.message import StreamMessage


class NatsMessage(StreamMessage[Msg]):
    """A class to represent a NATS message."""

    async def ack(self) -> None:
        # Check `self.raw_message._ackd` instead of `self.committed`
        # to be compatible with `self.raw_message.ack()`
        try:
            if not self.raw_message._ackd:
                await self.raw_message.ack()
        finally:
            await super().ack()

    async def ack_sync(self) -> None:
        try:
            if not self.raw_message._ackd:
                await self.raw_message.ack_sync()
        finally:
            await super().ack()

    async def nack(
        self,
        delay: Optional[float] = None,
    ) -> None:
        try:
            if not self.raw_message._ackd:
                await self.raw_message.nak(delay=delay)
        finally:
            await super().nack()

    async def reject(self) -> None:
        try:
            if not self.raw_message._ackd:
                await self.raw_message.term()
        finally:
            await super().reject()

    async def in_progress(self) -> None:
        if not self.raw_message._ackd:
            await self.raw_message.in_progress()


class NatsBatchMessage(StreamMessage[list[Msg]]):
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
        delay: Optional[float] = None,
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


class NatsKvMessage(StreamMessage[KeyValue.Entry]):
    pass


class NatsObjMessage(StreamMessage[ObjectInfo]):
    pass
