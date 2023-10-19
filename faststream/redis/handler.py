import asyncio
from functools import partial
from typing import Any, Awaitable, Callable, Dict, Hashable, Optional, Sequence

import anyio
from fast_depends.core import CallModel
from redis.asyncio.client import PubSub as RPubSub
from redis.asyncio.client import Redis

from faststream.broker.handler import AsyncHandler
from faststream.broker.message import StreamMessage
from faststream.broker.middlewares import BaseMiddleware
from faststream.broker.parsers import resolve_custom_func
from faststream.broker.types import (
    CustomDecoder,
    CustomParser,
    Filter,
    P_HandlerParams,
    T_HandlerReturn,
)
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.redis.message import PubSubMessage, RedisMessage
from faststream.redis.parser import RawMessage, RedisParser
from faststream.redis.schemas import ListSub, PubSub


class LogicRedisHandler(AsyncHandler[PubSubMessage]):
    subscription: Optional[RPubSub]
    task: Optional["asyncio.Task[Any]"]

    def __init__(
        self,
        *,
        log_context_builder: Callable[[StreamMessage[Any]], Dict[str, str]],
        # Redis info
        channel: Optional[PubSub] = None,
        list: Optional[ListSub] = None,
        # AsyncAPI information
        description: Optional[str] = None,
        title: Optional[str] = None,
        include_in_schema: bool = True,
    ):
        self.channel = channel
        self.list_sub = list

        self.subscription = None
        self.task = None

        super().__init__(
            log_context_builder=log_context_builder,
            description=description,
            title=title,
            include_in_schema=include_in_schema,
        )

    @property
    def channel_name(self) -> str:
        return (self.channel or self.list_sub).name

    def add_call(
        self,
        *,
        handler: HandlerCallWrapper[PubSubMessage, P_HandlerParams, T_HandlerReturn],
        dependant: CallModel[P_HandlerParams, T_HandlerReturn],
        parser: Optional[CustomParser[PubSubMessage, RedisMessage]],
        decoder: Optional[CustomDecoder[RedisMessage]],
        filter: Filter[RedisMessage],
        middlewares: Optional[Sequence[Callable[[PubSubMessage], BaseMiddleware]]],
    ) -> None:
        super().add_call(
            handler=handler,
            parser=resolve_custom_func(parser, RedisParser.parse_message),
            decoder=resolve_custom_func(decoder, RedisParser.decode_message),
            filter=filter,  # type: ignore[arg-type]
            dependant=dependant,
            middlewares=middlewares,
        )

    async def start(self, client: Redis) -> None:
        consume: Callable[[], Awaitable[PubSubMessage]]
        sleep: float

        if (list_sub := self.list_sub) is not None:
            sleep = list_sub.polling_interval
            consume = partial(
                consume_list_msg,
                client=client,
                name=list_sub.name,
                count=list_sub.records,
            )

        elif (channel := self.channel) is not None:
            self.subscription = psub = client.pubsub()

            if channel.pattern:
                await psub.psubscribe(channel.name)
            else:
                await psub.subscribe(channel.name)

            consume = partial(
                psub.get_message,
                ignore_subscribe_messages=True,
                timeout=channel.polling_interval,
            )
            sleep = 0.01

        else:
            raise AssertionError("unreachable")

        self.task = asyncio.create_task(self._consume(consume, sleep))

    async def close(self) -> None:
        if self.task is not None:
            self.task.cancel()
            self.task = None

        if self.subscription is not None:
            await self.subscription.unsubscribe()
            await self.subscription.aclose()
            self.subscription = None

    @staticmethod
    def get_routing_hash(channel: Hashable) -> int:
        return hash(channel)

    async def _consume(
        self,
        consume: Callable[[], Awaitable[Optional[PubSubMessage]]],
        sleep: float,
    ) -> None:
        connected = True
        while True:
            try:
                m = await consume()

            except Exception:
                if connected is True:
                    connected = False
                await anyio.sleep(5)

            else:
                if connected is False:
                    connected = True

                if m:  # pragma: no branch
                    await self.consume(m)

            finally:
                await anyio.sleep(sleep)


async def consume_list_msg(
    client: Redis,
    name: str,
    count: Optional[int],
) -> Optional[PubSubMessage]:
    msg = await client.lpop(name=name, count=count)

    if msg:
        if count is not None:
            msg = RawMessage.build(msg).data

        return PubSubMessage(
            type="message" if count is None else "batch",
            channel=name.encode(),
            data=msg,
        )
