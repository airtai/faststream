from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Union

from typing_extensions import TypedDict, override

from faststream.broker.message import StreamMessage as BrokerStreamMessage

if TYPE_CHECKING:
    from redis.asyncio import Redis


class BaseMessage(TypedDict):
    """A class to represent a Redis message."""
    type: str
    data: bytes
    channel: str


class PubSubMessage(BaseMessage):
    """A class to represent a PubSub message."""
    type: Literal["pmessage", "message"]
    pattern: Optional[bytes]


class ListMessage(BaseMessage):
    """A class to represent a List message."""
    type: Literal["list"]


class BatchListMessage(ListMessage):
    data: List[bytes]


class RedisBatchListMessage(BrokerStreamMessage[BatchListMessage]):
    body: List[Any]


StreamData = TypedDict("StreamData", {b"__data__": bytes}, total=True)


class StreamMessage(BaseMessage):
    type: Literal["stream"]
    message_ids: List[bytes]
    data: Union[StreamData, Dict[Any, Any]]


class BatchStreamMessage(StreamMessage):
    data: List[Union[StreamData, Dict[Any, Any]]]


class RedisStreamMessage(BrokerStreamMessage[StreamMessage]):
    body: List[Any]

    @override
    async def ack(  # type: ignore[override]
        self,
        redis: Optional["Redis[bytes]"] = None,
        group: Optional[str] = None,
    ) -> None:
        if not self.committed and group is not None and redis is not None:
            ids = self.raw_message["message_ids"]
            channel = self.raw_message["channel"]
            await redis.xack(channel, group, *ids)
            await super().ack()
