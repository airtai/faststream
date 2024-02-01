from abc import ABC
from contextlib import suppress
from functools import cached_property
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncContextManager,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
    Awaitable,
)

import anyio
from redis.asyncio.client import PubSub as RPubSub
from redis.asyncio.client import Redis
from typing_extensions import Annotated, Doc, override
from redis.exceptions import ResponseError

from faststream._compat import json_loads
from faststream.broker.core.handler import BaseHandler
from faststream.broker.core.publisher import FakePublisher
from faststream.broker.message import StreamMessage
from faststream.broker.parsers import resolve_custom_func
from faststream.redis.message import AnyRedisDict
from faststream.redis.parser import RawMessage, RedisParser, bDATA_KEY
from faststream.redis.schemas import ListSub, PubSub, StreamSub

if TYPE_CHECKING:
    from anyio.abc import TaskGroup, TaskStatus
    from fast_depends.dependencies import Depends

    from faststream.broker.core.handler_wrapper_mixin import WrapperProtocol
    from faststream.broker.message import StreamMessage
    from faststream.broker.types import (
        BrokerMiddleware,
        CustomDecoder,
        CustomParser,
        Filter,
        PublisherProtocol,
        SubscriberMiddleware,
    )
    from faststream.types import AnyDict


class BaseRedisHandler(ABC, BaseHandler[AnyRedisDict]):
    """A class to represent a Redis handler."""
    def __init__(
        self,
        *,
        watcher: Annotated[
            Callable[..., AsyncContextManager[None]],
            Doc("Watcher to ack message"),
        ],
        extra_context: Annotated[
            Optional["AnyDict"],
            Doc("Extra context to pass into consume scope"),
        ],
        graceful_timeout: Annotated[
            Optional[float],
            Doc(
                "Wait up to this time (if set) in graceful shutdown mode. "
                "Kills task forcefully if expired."
            ),
        ],
        middlewares: Annotated[
            Iterable["BrokerMiddleware[AnyRedisDict]"],
            Doc("Global middleware to use `on_receive`, `after_processed`"),
        ],
        # AsyncAPI information
        title_: Annotated[
            Optional[str],
            Doc("AsyncAPI subscriber title"),
        ],
        description_: Annotated[
            Optional[str],
            Doc("AsyncAPI subscriber description"),
        ],
        include_in_schema: Annotated[
            bool,
            Doc("Whether to include the handler in AsyncAPI schema"),
        ],
    ) -> None:
        self.channel = None
        self.list_sub = None
        self.stream_sub = None

        super().__init__(
            middlewares=middlewares,
            graceful_timeout=graceful_timeout,
            watcher=watcher,
            extra_context=extra_context,
            # AsyncAPI
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

    @override
    def add_call(  # type: ignore[override]
        self,
        *,
        filter: "Filter[StreamMessage[AnyRedisDict]]",
        parser: Optional["CustomParser[AnyRedisDict]"],
        decoder: Optional["CustomDecoder[StreamMessage[AnyRedisDict]]"],
        middlewares: Iterable["SubscriberMiddleware"],
        dependencies: Sequence["Depends"],
        **wrap_kwargs: Any,
    ) -> "WrapperProtocol[AnyRedisDict]":
        return super().add_call(
            parser_=resolve_custom_func(parser, RedisParser.parse_message),
            decoder_=resolve_custom_func(decoder, RedisParser.decode_message),
            filter_=filter,
            middlewares_=middlewares,
            dependencies_=dependencies,
            **wrap_kwargs,
        )

    def make_response_publisher(
        self, message: "StreamMessage[Any]"
    ) -> Sequence[FakePublisher]:
        if not message.reply_to or self.producer is None:
            return ()

        return (
            FakePublisher(
                self.producer.publish,
                channel=message.reply_to,
            ),
        )

    @override
    async def start(  # type: ignore[override]
        self,
        *args: Any,
        producer: Optional["PublisherProtocol"],
        task_group: "TaskGroup"
    ) -> None:
        await super().start(producer, task_group)
        await task_group.start(self._consume, *args)

    async def _consume(
        self,
        *args: Any,
        task_status: "TaskStatus[None]" = anyio.TASK_STATUS_IGNORED,
    ) -> None:
        connected = True
        started = False

        while self.running:
            with suppress(Exception):
                try:
                    await self._get_msgs(*args)

                except Exception:
                    if connected is True:
                        connected = False
                    await anyio.sleep(5)

                else:
                    if connected is False:
                        connected = True
                
                finally:
                    if not started:
                        started = True
                        task_status.started()

    @staticmethod
    def build_log_context(
        message: Optional["StreamMessage[Any]"],
        channel: str = "",
    ) -> Dict[str, str]:
        return {
            "channel": channel,
            "message_id": getattr(message, "message_id", ""),
        }

    def get_log_context(
        self,
        message: Optional["StreamMessage[Any]"],
    ) -> Dict[str, str]:
        return self.build_log_context(
            message=message,
            channel=self.channel_name,
        )


class ListHandler(BaseRedisHandler):
    def __init__(
        self,
        *,
        list: ListSub,
        # Base options
        watcher: Annotated[
            Callable[..., AsyncContextManager[None]],
            Doc("Watcher to ack message"),
        ],
        extra_context: Annotated[
            Optional["AnyDict"],
            Doc("Extra context to pass into consume scope"),
        ],
        graceful_timeout: Annotated[
            Optional[float],
            Doc(
                "Wait up to this time (if set) in graceful shutdown mode. "
                "Kills task forcefully if expired."
            ),
        ],
        middlewares: Annotated[
            Iterable["BrokerMiddleware[AnyRedisDict]"],
            Doc("Global middleware to use `on_receive`, `after_processed`"),
        ],
        # AsyncAPI information
        title_: Annotated[
            Optional[str],
            Doc("AsyncAPI subscriber title"),
        ],
        description_: Annotated[
            Optional[str],
            Doc("AsyncAPI subscriber description"),
        ],
        include_in_schema: Annotated[
            bool,
            Doc("Whether to include the handler in AsyncAPI schema"),
        ],
    ) -> None:
        super().__init__(
            middlewares=middlewares,
            graceful_timeout=graceful_timeout,
            watcher=watcher,
            extra_context=extra_context,
            # AsyncAPI
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

        self.list_sub = list

    @cached_property
    def channel_name(self) -> str:
        return self.list_sub.name

    @override
    async def start(  # type: ignore[override]
        self,
        client: "Redis[bytes]",
        *,
        producer: Optional["PublisherProtocol"],
        task_group: "TaskGroup"
    ) -> None:
        count = self.list_sub.records
        await super().start(client, count, producer=producer, task_group=task_group)

    async def _get_msgs(self, client: "Redis[bytes]", count: Optional[int]) -> None:
        msgs = await client.lpop(
            name=self.channel_name,
            count=count,
        )

        if msgs:
            if count is not None:
                parsed: List[Any] = []
                for m in msgs:
                    try:
                        data, _ = RedisParser.parse_one_msg(m)
                        data = json_loads(data)
                    except Exception:
                        data = m
                    parsed.append(data)
                
                await self.consume(AnyRedisDict(
                    type="batch",
                    channel=self.channel_name.encode(),
                    data=parsed
                ))
            
            else:
                await self.consume(AnyRedisDict(
                    type="list",
                    channel=self.channel_name.encode(),
                    data=msgs,
                ))

        else:
            await anyio.sleep(self.list_sub.polling_interval)


class ChannelHandler(BaseRedisHandler):
    subscription: Optional[RPubSub]

    def __init__(
        self,
        *,
        channel: PubSub,
        # Base options
        watcher: Annotated[
            Callable[..., AsyncContextManager[None]],
            Doc("Watcher to ack message"),
        ],
        extra_context: Annotated[
            Optional["AnyDict"],
            Doc("Extra context to pass into consume scope"),
        ],
        graceful_timeout: Annotated[
            Optional[float],
            Doc(
                "Wait up to this time (if set) in graceful shutdown mode. "
                "Kills task forcefully if expired."
            ),
        ],
        middlewares: Annotated[
            Iterable["BrokerMiddleware[AnyRedisDict]"],
            Doc("Global middleware to use `on_receive`, `after_processed`"),
        ],
        # AsyncAPI information
        title_: Annotated[
            Optional[str],
            Doc("AsyncAPI subscriber title"),
        ],
        description_: Annotated[
            Optional[str],
            Doc("AsyncAPI subscriber description"),
        ],
        include_in_schema: Annotated[
            bool,
            Doc("Whether to include the handler in AsyncAPI schema"),
        ],
    ) -> None:
        super().__init__(
            middlewares=middlewares,
            graceful_timeout=graceful_timeout,
            watcher=watcher,
            extra_context=extra_context,
            # AsyncAPI
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

        self.channel = channel
        self.subscription = None

    @cached_property
    def channel_name(self) -> str:
        return self.channel.name

    @override
    async def start(  # type: ignore[override]
        self,
        client: "Redis[bytes]",
        *,
        producer: Optional["PublisherProtocol"],
        task_group: "TaskGroup"
    ) -> None:
        self.subscription = psub = client.pubsub()

        if self.channel.pattern:
            await psub.psubscribe(self.channel.name)
        else:
            await psub.subscribe(self.channel.name)
        
        await super().start(psub, producer=producer, task_group=task_group)

    async def _consume(
        self,
        psub: RPubSub,
        task_status: "TaskStatus[None]" = anyio.TASK_STATUS_IGNORED,
    ) -> None:
        await super()._consume(psub, task_status=task_status)
    
    async def _get_msgs(self, psub: RPubSub):
        msg = await psub.get_message(
            ignore_subscribe_messages=True,
            timeout=self.channel.polling_interval,
        )
        if msg:
            await self.consume(msg)

    async def close(self) -> None:
        await super().close()

        if self.subscription is not None:
            await self.subscription.unsubscribe()
            await self.subscription.aclose()  # type: ignore[attr-defined]
            self.subscription = None


class StreamHandler(BaseRedisHandler):
    def __init__(
        self,
        *,
        stream: StreamSub,
        # Base options
        watcher: Annotated[
            Callable[..., AsyncContextManager[None]],
            Doc("Watcher to ack message"),
        ],
        extra_context: Annotated[
            Optional["AnyDict"],
            Doc("Extra context to pass into consume scope"),
        ],
        graceful_timeout: Annotated[
            Optional[float],
            Doc(
                "Wait up to this time (if set) in graceful shutdown mode. "
                "Kills task forcefully if expired."
            ),
        ],
        middlewares: Annotated[
            Iterable["BrokerMiddleware[AnyRedisDict]"],
            Doc("Global middleware to use `on_receive`, `after_processed`"),
        ],
        # AsyncAPI information
        title_: Annotated[
            Optional[str],
            Doc("AsyncAPI subscriber title"),
        ],
        description_: Annotated[
            Optional[str],
            Doc("AsyncAPI subscriber description"),
        ],
        include_in_schema: Annotated[
            bool,
            Doc("Whether to include the handler in AsyncAPI schema"),
        ],
    ) -> None:
        super().__init__(
            middlewares=middlewares,
            graceful_timeout=graceful_timeout,
            watcher=watcher,
            extra_context=extra_context,
            # AsyncAPI
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

        self.stream_sub = stream
        self.last_id = stream.last_id if stream else "$"

    @cached_property
    def channel_name(self) -> str:
        return self.stream_sub.name
    
    @override
    async def start(  # type: ignore[override]
        self,
        client: "Redis[bytes]",
        *,
        producer: Optional["PublisherProtocol"],
        task_group: "TaskGroup"
    ) -> None:
        stream = self.stream_sub

        if stream.group and stream.consumer:
            try:
                await client.xgroup_create(
                    name=stream.name,
                    groupname=stream.group,
                    mkstream=True,
                )
            except ResponseError as e:
                if "already exists" not in str(e):
                    raise e

            read = lambda _: client.xreadgroup(
                groupname=stream.group,
                consumername=stream.consumer,
                streams={stream.name: ">"},
                block=stream.polling_interval,
                noack=stream.no_ack,
            )

        else:
            read = lambda last_id: client.xread(
                {stream.name: last_id},
                block=stream.polling_interval,
            )

        await super().start(read, producer=producer, task_group=task_group)

    async def _get_msgs(
        self,
        read: Callable[
            [str],
            Awaitable[Tuple[Tuple[bytes, Tuple[Tuple[bytes, Dict[Any, Any]], ...]], ...],],
        ]
    ) -> Union[None, AnyRedisDict, Iterable[AnyRedisDict]]:
        for stream_name, msgs in await read(self.last_id):
            if msgs:
                self.last_id = msgs[-1][0].decode()

                if self.stream_sub.batch:
                    parsed: List[Any] = []
                    ids = []
                    for message_id, msg in msgs:
                        ids.append(message_id.decode())

                        m = msg.get(bDATA_KEY, msg)
                        try:
                            data, _ = RedisParser.parse_one_msg(m)
                            data = json_loads(data)
                        except Exception:
                            data = m
                        parsed.append(data)

                    await self.consume(
                        AnyRedisDict(
                            type="batch",
                            channel=stream_name,
                            data=parsed,
                            message_id=ids[0],
                            message_ids=ids,
                        )
                    )

                else:
                    for message_id, msg in msgs:
                        await self.consume(
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
                        )
