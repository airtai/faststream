import asyncio
import json
from functools import partial
from typing import Any, Awaitable, Callable, Dict, Optional, Sequence

import anyio
from fast_depends.core import CallModel
from redis.asyncio.client import PubSub, Redis

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
from faststream.redis.parser import RedisParser
from faststream.utils.context.path import compile_path


class LogicRedisHandler(AsyncHandler[PubSubMessage]):
    subscription: Optional[PubSub]
    task: Optional["asyncio.Task[Any]"]

    def __init__(
        self,
        channel: str,
        log_context_builder: Callable[[StreamMessage[Any]], Dict[str, str]],
        # Redis info
        pattern: bool = False,
        list: bool = False,
        batch: bool = False,
        max_records: int = 10,
        polling_interval: Optional[float] = None,
        # AsyncAPI information
        description: Optional[str] = None,
        title: Optional[str] = None,
        include_in_schema: bool = True,
    ):
        reg, path = compile_path(channel, replace_symbol="*")

        if list and reg:
            raise ValueError("You can't use pattern with `list` subscriber type")

        self.path_regex = reg
        self.channel = path
        self.pattern = pattern

        self.list = list
        self.batch = batch
        self.max_records = max_records

        self.polling_interval = polling_interval

        self.subscription = None
        self.task = None

        super().__init__(
            log_context_builder=log_context_builder,
            description=description,
            title=title,
            include_in_schema=include_in_schema,
        )

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

        if self.list:
            sleep = self.polling_interval or 0.1
            consume = partial(
                consume_list_msg,
                client=client,
                name=self.channel,
                count=self.max_records if self.batch else None,
            )

        else:
            self.subscription = psub = client.pubsub()

            if self.pattern is True:
                await psub.psubscribe(self.channel)
            else:
                await psub.subscribe(self.channel)

            consume = partial(
                psub.get_message,
                ignore_subscribe_messages=True,
                timeout=self.polling_interval or 1.0,
            )
            sleep = 0.01

        self.task = asyncio.create_task(self._consume(consume, sleep))

    async def close(self) -> None:
        if self.task is not None:
            self.task.cancel()
            self.task = None

        if self.subscription is not None:
            await self.subscription.unsubscribe()
            await self.subscription.reset()
            self.subscription = None

    @staticmethod
    def get_routing_hash(channel: str) -> str:
        return channel

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
        if isinstance(msg, list):
            msg = json.dumps([x.decode() for x in msg]).encode()

        return PubSubMessage(
            type="message",
            channel=name.encode(),
            data=msg,
        )
