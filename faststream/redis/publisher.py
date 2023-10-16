from dataclasses import dataclass, field
from typing import Optional

from faststream._compat import override
from faststream.broker.publisher import BasePublisher
from faststream.redis.message import PubSubMessage
from faststream.redis.producer import RedisFastProducer
from faststream.types import AnyDict, DecodedMessage, SendableMessage


@dataclass
class LogicPublisher(BasePublisher[PubSubMessage]):
    channel: str = field(default="")
    reply_to: str = field(default="")
    headers: Optional[AnyDict] = field(default=None)

    _producer: Optional[RedisFastProducer] = field(default=None, init=False)

    @override
    async def publish(  # type: ignore[override]
        self,
        message: SendableMessage,
        channel: str = "",
        reply_to: str = "",
        headers: Optional[AnyDict] = None,
        correlation_id: Optional[str] = None,
        *,
        rpc: bool = False,
        rpc_timeout: Optional[float] = 30.0,
        raise_timeout: bool = False,
    ) -> Optional[DecodedMessage]:
        assert self._producer, "Please, `connect()` the broker first"  # nosec B101
        assert self.channel, "You have to specify outgoing channel"  # nosec B101

        headers_to_send = (self.headers or {}).copy()
        if headers is not None:
            headers_to_send.update(headers)

        return await self._producer.publish(
            message=message,
            channel=channel or self.channel,
            reply_to=reply_to or self.reply_to,
            correlation_id=correlation_id,
            headers=headers_to_send,
            rpc=rpc,
            rpc_timeout=rpc_timeout,
            raise_timeout=raise_timeout,
        )
