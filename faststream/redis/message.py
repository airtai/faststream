from typing import Any, List, Literal, Optional, TypeVar, Union

from redis.asyncio import Redis

from faststream._compat import NotRequired, TypedDict, override
from faststream.broker.message import StreamMessage
from faststream.utils.context.main import context


class PubSubMessage(TypedDict):
    """A class to represent a PubSub message."""

    channel: bytes
    data: Union[bytes, List[bytes]]
    type: str
    message_id: NotRequired[str]
    message_ids: NotRequired[List[str]]


class OneMessage(PubSubMessage):
    """A class to represent a PubSub message."""

    type: Literal["stream", "list", "message"]  # type: ignore[misc]
    data: bytes  # type: ignore[misc]
    pattern: NotRequired[Optional[bytes]]


class BatchMessage(PubSubMessage):
    """A class to represent a PubSub message."""

    type: Literal["batch"]  # type: ignore[misc]
    data: List[bytes]  # type: ignore[misc]


class AnyRedisDict(PubSubMessage):
    """A class to represent a PubSub message."""

    type: Literal["stream", "list", "message", "batch"]  # type: ignore[misc]
    data: Union[bytes, List[bytes]]  # type: ignore[misc]
    pattern: NotRequired[Optional[bytes]]


MsgType = TypeVar("MsgType", OneMessage, BatchMessage, AnyRedisDict)


class RedisAckMixin(StreamMessage[MsgType]):
    """A class to represent a Redis ACK mixin."""

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


class RedisMessage(RedisAckMixin[AnyRedisDict]):
    """A class to represent a Redis message."""

    pass


class OneRedisMessage(RedisAckMixin[OneMessage]):
    """A class to represent a Redis message."""

    pass


class BatchRedisMessage(RedisAckMixin[BatchMessage]):
    """A class to represent a Redis batch of messages."""

    pass
