from typing import Any, Optional

from redis.asyncio import Redis

from faststream._compat import NotRequired, TypedDict
from faststream.broker.message import StreamMessage
from faststream.utils.context.main import context


class PubSubMessage(TypedDict):
    type: str
    pattern: NotRequired[Optional[bytes]]
    channel: NotRequired[bytes]
    data: bytes
    message_id: NotRequired[str]
    message_ids: NotRequired[list[str]]


class RedisMessage(StreamMessage[PubSubMessage]):
    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.commited = False

    async def ack(self, redis: Redis, **kwargs: Any) -> None:
        if (
            not self.commited
            and (ids := self.raw_message.get("message_ids"))
            and (handler := context.get_local("handler_"))
            and (stream := handler.stream_sub)
            and (group := stream.group)
        ):
            await redis.xack(self.raw_message["channel"], group, *ids)

        self.commited = True

    async def nack(self, **kwargs: Any) -> None:
        self.commited = True

    async def reject(self, **kwargs: Any) -> None:
        self.commited = True
