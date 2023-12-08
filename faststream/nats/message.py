from dataclasses import dataclass
from typing import Any

from nats.aio.msg import Msg

from faststream.broker.message import StreamMessage


@dataclass
class NatsMessage(StreamMessage[Msg]):
    is_js: bool = True

    async def ack(self, **kwargs: Any) -> None:
        await super().ack()
        if self.is_js:
            if not isinstance(self.raw_message, list):
                if not self.raw_message._ackd:
                    await self.raw_message.ack()

            else:
                for m in filter(
                    lambda m: not m._ackd,
                    self.raw_message,
                ):
                    await m.ack()

    async def nack(self, **kwargs: Any) -> None:
        await super().nack()
        if self.is_js:
            if not isinstance(self.raw_message, list):
                if not self.raw_message._ackd:
                    await self.raw_message.nak(**kwargs)

            else:
                for m in filter(
                    lambda m: not m._ackd,
                    self.raw_message,
                ):
                    await m.nak(**kwargs)

    async def reject(self, **kwargs: Any) -> None:
        await super().reject()
        if self.is_js:
            if not isinstance(self.raw_message, list):
                if not self.raw_message._ackd:
                    await self.raw_message.term()

            else:
                for m in filter(
                    lambda m: not m._ackd,
                    self.raw_message,
                ):
                    await m.term()

    async def in_progress(self, **kwargs: Any) -> None:
        if self.is_js:
            if not isinstance(self.raw_message, list):
                if not self.raw_message._ackd:
                    await self.raw_message.in_progress()

            else:
                for m in filter(
                    lambda m: not m._ackd,
                    self.raw_message,
                ):
                    await m.in_progress()
