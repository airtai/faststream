from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, Any, Iterable, Optional, Sequence, Union, cast

from typing_extensions import override

from faststream.broker.core.publisher import BasePublisher
from faststream.exceptions import NOT_CONNECTED_YET
from faststream.redis.producer import RedisFastProducer
from faststream.redis.schemas import INCORRECT_SETUP_MSG, ListSub, PubSub, StreamSub
from faststream.types import AnyDict, DecodedMessage, SendableMessage

if TYPE_CHECKING:
    from faststream.broker.types import PublisherMiddleware

@dataclass
class LogicPublisher(BasePublisher["AnyRedisDict"]):
    """A class to represent a Redis publisher."""

    channel: Optional[PubSub]
    list: Optional[ListSub]
    stream: Optional[StreamSub]
    reply_to: str
    headers: Optional[AnyDict]

    _producer: Optional[RedisFastProducer]

    def __init__(
        self,
        *,
        channel: Optional[PubSub],
        list: Optional[ListSub],
        stream: Optional[StreamSub],
        reply_to: str,
        headers: Optional[AnyDict],
        # Regular publisher options
        middlewares: Iterable["PublisherMiddleware"],
        # AsyncAPI options
        schema_: Optional[Any],
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        """Initialize NATS publisher object."""
        super().__init__(
            middlewares=middlewares,
            schema_=schema_,
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

        self.channel = channel
        self.list = list
        self.stream = stream
        self.reply_to = reply_to
        self.headers = headers

        self._producer = None

    @override
    async def _publish(  # type: ignore[override]
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

        if (list := ListSub.validate(list)) is not None:
            if list.batch:
                await self._producer.publish_batch(
                    *cast(Sequence[SendableMessage], message),
                    list=list.name,  # type: ignore[union-attr]
                )
                return None
            else:
                kwargs = {"list": list.name}

        elif channel := PubSub.validate(channel):
            kwargs = {"channel": channel.name}

        elif stream := StreamSub.validate(stream):
            kwargs = {
                "stream": stream.name,
                "maxlen": stream.maxlen,
            }

        else:
            raise ValueError(INCORRECT_SETUP_MSG)

        return await self._producer.publish(
            message=message,
            **kwargs,
            reply_to=reply_to,
            correlation_id=correlation_id,
            headers=headers,
            rpc=rpc,
            rpc_timeout=rpc_timeout,
            raise_timeout=raise_timeout,
        )

    @cached_property
    def channel_name(self) -> str:
        any_of = self.channel or self.list or self.stream
        assert any_of, INCORRECT_SETUP_MSG  # nosec B101
        return any_of.name

    @cached_property
    def publish_kwargs(self) -> AnyDict:
        return {
            "channel": self.channel,
            "list": self.list,
            "stream": self.stream,
            "headers": self.headers,
            "reply_to": self.reply_to,
        }
