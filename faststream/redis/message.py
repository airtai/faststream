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


class RedisMessage(StreamMessage[PubSubMessage]):
    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.commited = False

    @override
    async def ack(  # type: ignore[override]
        self,
        redis: Redis[Any],
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

        self.commited = True

    async def nack(self, **kwargs: Any) -> None:
        self.commited = True

    async def reject(self, **kwargs: Any) -> None:
        self.commited = True
