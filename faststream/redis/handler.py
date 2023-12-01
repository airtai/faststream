import asyncio
import json
from contextlib import suppress
from functools import partial
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Generator,
    Hashable,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
    cast,
)

import anyio
from fast_depends.core import CallModel
from redis.asyncio.client import PubSub as RPubSub
from redis.asyncio.client import Redis

from faststream._compat import override
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
from faststream.redis.message import (
    AnyRedisDict,
    RedisMessage,
)
from faststream.redis.parser import RawMessage, RedisParser, bDATA_KEY
from faststream.redis.schemas import INCORRECT_SETUP_MSG, ListSub, PubSub, StreamSub
from faststream.types import AnyDict


class LogicRedisHandler(AsyncHandler[AnyRedisDict]):
    subscription: Optional[RPubSub]
    task: Optional["asyncio.Task[Any]"]

    def __init__(
        self,
        *,
        log_context_builder: Callable[[StreamMessage[Any]], Dict[str, str]],
        # Redis info
        channel: Optional[PubSub] = None,
        list: Optional[ListSub] = None,
        stream: Optional[StreamSub] = None,
        last_id: str = "$",
        # AsyncAPI information
        description: Optional[str] = None,
        title: Optional[str] = None,
        include_in_schema: bool = True,
    ):
        self.channel = channel
        self.list_sub = list
        self.stream_sub = stream

        self.subscription = None
        self.task = None

        self.last_id = last_id

        super().__init__(
            log_context_builder=log_context_builder,
            description=description,
            title=title,
            include_in_schema=include_in_schema,
        )

    @property
    def channel_name(self) -> str:
        any_of = self.channel or self.list_sub or self.stream_sub
        assert any_of, INCORRECT_SETUP_MSG  # nosec B101
        return any_of.name

    def add_call(
        self,
        *,
        handler: HandlerCallWrapper[AnyDict, P_HandlerParams, T_HandlerReturn],
        dependant: CallModel[P_HandlerParams, T_HandlerReturn],
        parser: Optional[CustomParser[AnyDict, RedisMessage]],
        decoder: Optional[CustomDecoder[RedisMessage]],
        filter: Filter[RedisMessage],
        middlewares: Optional[Sequence[Callable[[AnyDict], BaseMiddleware]]],
    ) -> None:
        super().add_call(
            handler=handler,
            parser=resolve_custom_func(parser, RedisParser.parse_message),
            decoder=resolve_custom_func(decoder, RedisParser.decode_message),
            filter=filter,  # type: ignore[arg-type]
            dependant=dependant,
            middlewares=middlewares,
        )

    @override
    async def start(self, client: "Redis[bytes]") -> None:  # type: ignore[override]
        self.started = anyio.Event()

        consume: Union[
            Callable[[], Awaitable[Optional[AnyRedisDict]]],
            Callable[[], Awaitable[Optional[Sequence[AnyRedisDict]]]],
        ]
        sleep: float

        if (list_sub := self.list_sub) is not None:
            sleep = list_sub.polling_interval
            consume = partial(
                self._consume_list_msg,
                client=client,
            )
            self.started.set()

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
            self.started.set()

        elif self.stream_sub is not None:
            consume = partial(  # type: ignore[assignment]
                self._consume_stream_msg,
                client=client,
            )
            sleep = 0.01

        else:
            raise AssertionError("unreachable")

        await super().start()
        self.task = asyncio.create_task(self._consume(consume, sleep))
        # wait until Stream starts to consume
        await anyio.sleep(0.01)
        await self.started.wait()

    async def close(self) -> None:
        await super().close()

        if self.task is not None:
            if not self.task.done():
                self.task.cancel()
            self.task = None

        if self.subscription is not None:
            await self.subscription.unsubscribe()
            await self.subscription.aclose()  # type: ignore[attr-defined]
            self.subscription = None

    @staticmethod
    def get_routing_hash(channel: Hashable) -> int:
        return hash(channel)

    async def _consume(
        self,
        consume: Union[
            Callable[[], Awaitable[Optional[AnyRedisDict]]],
            Callable[[], Awaitable[Optional[Sequence[AnyRedisDict]]]],
        ],
        sleep: float,
    ) -> None:
        connected = True

        while self.running:
            with suppress(Exception):
                try:
                    m = await consume()

                except Exception:
                    if connected is True:
                        connected = False
                    await anyio.sleep(5)

                else:
                    if connected is False:
                        connected = True

                    if msgs := (
                        (m,) if isinstance(m, dict) else m
                    ):  # pragma: no branch
                        for i in msgs:
                            await self.consume(i)

                finally:
                    await anyio.sleep(sleep)

    async def _consume_stream_msg(
        self,
        client: "Redis[bytes]",
    ) -> Union[None, AnyRedisDict, Generator[AnyRedisDict, None, None]]:
        stream = self.stream_sub
        assert stream  # nosec B101

        if stream.group and stream.consumer:
            read = client.xreadgroup(
                groupname=stream.group,
                consumername=stream.consumer,
                streams={stream.name: ">"},
                block=stream.polling_interval,
                noack=stream.no_ack,
            )

        else:
            read = client.xread(
                {stream.name: self.last_id},
                block=stream.polling_interval,
            )

        self.started.set()

        for stream_name, msgs in cast(
            Tuple[Tuple[bytes, Tuple[Tuple[bytes, AnyDict], ...]], ...],
            await read,
        ):
            if msgs:
                self.last_id = msgs[-1][0].decode()

                if stream.batch:
                    parsed: List[Any] = []
                    ids = []
                    for message_id, msg in msgs:
                        ids.append(message_id.decode())

                        m = msg.get(bDATA_KEY, msg)
                        try:
                            data, _ = RedisParser.parse_one_msg(m)
                            data = json.loads(data)
                        except Exception:
                            data = m
                        parsed.append(data)

                    return AnyRedisDict(
                        type="batch",
                        channel=stream_name,
                        data=parsed,
                        message_id=ids[0],
                        message_ids=ids,
                    )

                else:
                    return (
                        AnyRedisDict(
                            type="stream",
                            channel=stream_name,
                            data=msg.get(
                                bDATA_KEY,
                                RawMessage.encode(message=msg).encode(),
                            ),
                            message_id=message_id.decode(),
                            message_ids=[message_id.decode()],
                        )
                        for message_id, msg in msgs
                    )

        return None

    async def _consume_list_msg(
        self,
        client: "Redis[bytes]",
    ) -> Optional[AnyRedisDict]:
        list_sub = self.list_sub
        assert list_sub  # nosec B101

        count = list_sub.records

        msg = await client.lpop(name=list_sub.name, count=count)

        if msg:
            if count is not None:
                parsed: List[Any] = []
                for m in msg:
                    try:
                        data, _ = RedisParser.parse_one_msg(m)
                        data = json.loads(data)
                    except Exception:
                        data = m
                    parsed.append(data)
                msg = parsed

            if count is None:
                return AnyRedisDict(
                    type="list",
                    channel=list_sub.name.encode(),
                    data=msg,
                )

            else:
                return AnyRedisDict(
                    type="batch",
                    channel=list_sub.name.encode(),
                    data=msg,
                )

        return None
