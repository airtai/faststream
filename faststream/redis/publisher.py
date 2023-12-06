from dataclasses import dataclass, field
from typing import Optional, Union

from faststream._compat import override
from faststream.broker.publisher import BasePublisher
from faststream.exceptions import NOT_CONNECTED_YET
from faststream.redis.message import AnyRedisDict
from faststream.redis.producer import RedisFastProducer
from faststream.redis.schemas import INCORRECT_SETUP_MSG, ListSub, PubSub, StreamSub
from faststream.types import AnyDict, DecodedMessage, SendableMessage


@dataclass
class LogicPublisher(BasePublisher[AnyRedisDict]):
    channel: Optional[PubSub] = field(default=None)
    list: Optional[ListSub] = field(default=None)
    stream: Optional[StreamSub] = field(default=None)
    reply_to: str = field(default="")
    headers: Optional[AnyDict] = field(default=None)

    _producer: Optional[RedisFastProducer] = field(default=None, init=False)

    @override
    async def publish(  # type: ignore[override]
        self,
        message: SendableMessage,
        channel: Union[str, PubSub, None] = None,
        reply_to: str = "",
        headers: Optional[AnyDict] = None,
        correlation_id: Optional[str] = None,
        *,
        list: Union[str, ListSub, None] = None,
        stream: Union[str, StreamSub, None] = None,
        rpc: bool = False,
        rpc_timeout: Optional[float] = 30.0,
        raise_timeout: bool = False,
    ) -> Optional[DecodedMessage]:
        assert self._producer, NOT_CONNECTED_YET  # nosec B101

        channel = PubSub.validate(channel or self.channel)
        list = ListSub.validate(list or self.list)
        stream = StreamSub.validate(stream or self.stream)

        assert any(
            (channel, list, stream)
        ), "You have to specify outgoing channel"  # nosec B101

        headers_to_send = (self.headers or {}).copy()
        if headers is not None:
            headers_to_send.update(headers)

        if getattr(list, "batch", False):
            await self._producer.publish_batch(
                *message,
                list=list.name,  # type: ignore[union-attr]
            )
            return None

        else:
            return await self._producer.publish(
                message=message,
                channel=getattr(channel, "name", None),
                list=getattr(list, "name", None),
                stream=getattr(stream, "name", None),
                reply_to=reply_to or self.reply_to,
                correlation_id=correlation_id,
                headers=headers_to_send,
                rpc=rpc,
                rpc_timeout=rpc_timeout,
                raise_timeout=raise_timeout,
            )

    @property
    def channel_name(self) -> str:
        any_of = self.channel or self.list or self.stream
        assert any_of, INCORRECT_SETUP_MSG  # nosec B101
        return any_of.name
