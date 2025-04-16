from collections.abc import Iterable, Sequence
from copy import deepcopy
from typing import (
    TYPE_CHECKING,
    Any,
    Optional,
)

import anyio
from redis.asyncio.client import (
    PubSub as RPubSub,
)
from typing_extensions import TypeAlias, override

from faststream._internal.subscriber.mixins import ConcurrentMixin
from faststream._internal.subscriber.utils import process_msg
from faststream.middlewares import AckPolicy
from faststream.redis.message import (
    PubSubMessage,
    RedisMessage,
    UnifyRedisDict,
)
from faststream.redis.parser import (
    RedisPubSubParser,
)

from .basic import LogicSubscriber

if TYPE_CHECKING:
    from fast_depends.dependencies import Dependant

    from faststream._internal.types import (
        BrokerMiddleware,
    )
    from faststream.message import StreamMessage as BrokerStreamMessage
    from faststream.redis.schemas import PubSub


TopicName: TypeAlias = bytes
Offset: TypeAlias = bytes


class ChannelSubscriber(LogicSubscriber):
    subscription: Optional[RPubSub]

    def __init__(
        self,
        *,
        channel: "PubSub",
        # Subscriber args
        no_reply: bool,
        broker_dependencies: Iterable["Dependant"],
        broker_middlewares: Sequence["BrokerMiddleware[UnifyRedisDict]"],
    ) -> None:
        parser = RedisPubSubParser(pattern=channel.path_regex)
        super().__init__(
            default_parser=parser.parse_message,
            default_decoder=parser.decode_message,
            # Propagated options
            ack_policy=AckPolicy.DO_NOTHING,
            no_reply=no_reply,
            broker_middlewares=broker_middlewares,
            broker_dependencies=broker_dependencies,
        )

        self.channel = channel
        self.subscription = None

    def get_log_context(
        self,
        message: Optional["BrokerStreamMessage[Any]"],
    ) -> dict[str, str]:
        return self.build_log_context(
            message=message,
            channel=self.channel.name,
        )

    @override
    async def start(self) -> None:
        if self.subscription:
            return

        assert self._client, "You should setup subscriber at first."  # nosec B101

        self.subscription = psub = self._client.pubsub()

        if self.channel.pattern:
            await psub.psubscribe(self.channel.name)
        else:
            await psub.subscribe(self.channel.name)

        await super().start(psub)

    async def close(self) -> None:
        if self.subscription is not None:
            await self.subscription.unsubscribe()
            await self.subscription.aclose()  # type: ignore[attr-defined]
            self.subscription = None

        await super().close()

    @override
    async def get_one(
        self,
        *,
        timeout: float = 5.0,
    ) -> "Optional[RedisMessage]":
        assert self.subscription, "You should start subscriber at first."  # nosec B101
        assert (  # nosec B101
            not self.calls
        ), "You can't use `get_one` method if subscriber has registered handlers."

        sleep_interval = timeout / 10

        raw_message: Optional[PubSubMessage] = None

        with anyio.move_on_after(timeout):
            while (raw_message := await self._get_message(self.subscription)) is None:  # noqa: ASYNC110
                await anyio.sleep(sleep_interval)

        context = self._state.get().di_state.context

        msg: Optional[RedisMessage] = await process_msg(  # type: ignore[assignment]
            msg=raw_message,
            middlewares=(
                m(raw_message, context=context) for m in self._broker_middlewares
            ),
            parser=self._parser,
            decoder=self._decoder,
        )
        return msg

    async def _get_message(self, psub: RPubSub) -> Optional[PubSubMessage]:
        raw_msg = await psub.get_message(
            ignore_subscribe_messages=True,
            timeout=self.channel.polling_interval,
        )

        if raw_msg:
            return PubSubMessage(
                type=raw_msg["type"],
                data=raw_msg["data"],
                channel=raw_msg["channel"].decode(),
                pattern=raw_msg["pattern"],
            )

        return None

    async def _get_msgs(self, psub: RPubSub) -> None:
        if msg := await self._get_message(psub):
            await self.consume_one(msg)

    def add_prefix(self, prefix: str) -> None:
        new_ch = deepcopy(self.channel)
        new_ch.name = f"{prefix}{new_ch.name}"
        self.channel = new_ch


class ConcurrentChannelSubscriber(
    ConcurrentMixin["BrokerStreamMessage"], ChannelSubscriber
):
    def __init__(
        self,
        *,
        channel: "PubSub",
        # Subscriber args
        no_reply: bool,
        broker_dependencies: Iterable["Dependant"],
        broker_middlewares: Sequence["BrokerMiddleware[UnifyRedisDict]"],
        # AsyncAPI args
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
        max_workers: int,
    ) -> None:
        super().__init__(
            # Propagated options
            channel=channel,
            no_reply=no_reply,
            max_workers=max_workers,
            broker_middlewares=broker_middlewares,
            broker_dependencies=broker_dependencies,
            # AsyncAPI
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

    async def start(self) -> None:
        await super().start()
        self.start_consume_task()

    async def consume_one(self, msg: "BrokerStreamMessage") -> None:
        await self._put_msg(msg)
