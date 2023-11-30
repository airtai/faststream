from dataclasses import dataclass
from typing import Any

from nats.aio.msg import Msg

from faststream.broker.message import StreamMessage


@dataclass
class NatsMessage(StreamMessage[Msg]):
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
