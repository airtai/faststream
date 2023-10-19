from typing import Any, Optional

from faststream._compat import NotRequired, TypedDict
from faststream.broker.message import StreamMessage


class PubSubMessage(TypedDict):
    type: str
    pattern: NotRequired[Optional[bytes]]
    channel: bytes
    data: bytes


class RedisMessage(StreamMessage[PubSubMessage]):
    async def ack(self, **kwargs: Any) -> None:
        self.commited = True

    async def nack(self, **kwargs: Any) -> None:
        self.commited = True

    async def reject(self, **kwargs: Any) -> None:
        self.commited = True
