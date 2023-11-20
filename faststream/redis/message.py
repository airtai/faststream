from typing import Any, List, Literal, Optional, Union

from redis.asyncio import Redis

from faststream._compat import NotRequired, TypedDict, override
from faststream.broker.message import StreamMessage
from faststream.utils.context.main import context


class PubSubMessage(TypedDict):
    channel: bytes
    data: Union[bytes, List[bytes]]
    type: str
    message_id: NotRequired[str]
    message_ids: NotRequired[List[str]]


class OneMessage(PubSubMessage):
    type: Literal["stream", "list", "message"]  # type: ignore[misc]
    data: bytes  # type: ignore[misc]
    pattern: NotRequired[Optional[bytes]]


class BatchMessage(PubSubMessage):
    type: Literal["batch"]  # type: ignore[misc]
    data: List[bytes]  # type: ignore[misc]


class AnyRedisDict(PubSubMessage):
    type: Literal["stream", "list", "message", "batch"]  # type: ignore[misc]
    data: Union[bytes, List[bytes]]  # type: ignore[misc]
    pattern: NotRequired[Optional[bytes]]


class RedisMessage(StreamMessage[AnyRedisDict]):
    pass


class OneRedisMessage(StreamMessage[OneMessage]):
    pass


class BatchRedisMessage(StreamMessage[BatchMessage]):
    @override
    async def ack(  # type: ignore[override]
        self,
        redis: "Redis[bytes]",
        **kwargs: Any,
    ) -> None:
        if (
            not self.commited
            and (ids := self.raw_message.get("message_ids"))
            and (handler := context.get_local("handler_"))
            and (stream := handler.stream_sub)
            and (group := stream.group)
        ):
            await redis.xack(self.raw_message["channel"], group, *ids)  # type: ignore[no-untyped-call]

            await super().ack()
