import asyncio
from abc import ABC, abstractmethod, abstractproperty
from contextlib import suppress
from functools import cached_property
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncContextManager,
    Awaitable,
    Callable,
    Dict,
    Iterable,
    Optional,
    Sequence,
    Tuple,
)

import anyio
from redis.asyncio.client import PubSub as RPubSub
from redis.asyncio.client import Redis
from redis.exceptions import ResponseError
from typing_extensions import Annotated, Doc, override

from faststream.broker.core.handler import BaseHandler
from faststream.broker.core.publisher import FakePublisher
from faststream.broker.parsers import resolve_custom_func
from faststream.broker.types import MsgType
from faststream.redis.message import (
    BatchListMessage,
    BatchStreamMessage,
    ListMessage,
    PubSubMessage,
    StreamMessage,
)
from faststream.redis.parser import (
    RedisBatchListParser,
    RedisBatchStreamParser,
    RedisListParser,
    RedisPubSubParser,
    RedisStreamParser,
)
from faststream.redis.schemas import ListSub, PubSub, StreamSub

if TYPE_CHECKING:
    from fast_depends.dependencies import Depends

    from faststream.broker.core.handler_wrapper_mixin import WrapperProtocol
    from faststream.broker.message import StreamMessage as BrokerStreamMessage
    from faststream.broker.types import (
        BrokerMiddleware,
        CustomDecoder,
        CustomParser,
        Filter,
        PublisherProtocol,
        SubscriberMiddleware,
    )
    from faststream.types import AnyDict


class BaseRedisHandler(ABC, BaseHandler[MsgType]):
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
            Iterable["BrokerMiddleware[MsgType]"],
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

        self.task: Optional["asyncio.Task[None]"] = None

    @override
    def add_call(  # type: ignore[override]
        self,
        *,
        filter: "Filter[BrokerStreamMessage[MsgType]]",
        parser: Optional["CustomParser[MsgType]"],
        decoder: Optional["CustomDecoder[BrokerStreamMessage[MsgType]]"],
        middlewares: Iterable["SubscriberMiddleware"],
        dependencies: Sequence["Depends"],
        **wrap_kwargs: Any,
    ) -> "WrapperProtocol[MsgType]":
        return super().add_call(
            parser_=parser,
            decoder_=decoder,
            filter_=filter,
            middlewares_=middlewares,
            dependencies_=dependencies,
            **wrap_kwargs,
        )

    def make_response_publisher(
        self, message: "BrokerStreamMessage[MsgType]"
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
    ) -> None:
        await super().start(producer)

        start_signal = anyio.Event()
        self.task = asyncio.create_task(self._consume(*args, start_signal=start_signal))
        await start_signal.wait()

    async def _consume(self, *args: Any, start_signal: anyio.Event) -> None:
        connected = True

        while self.running:
            with suppress(Exception):
                try:
                    await self._get_msgs(*args)

                except Exception:
                    if connected:
                        connected = False
                    await anyio.sleep(5)

                else:
                    if not connected:
                        connected = True

                finally:
                    if not start_signal.is_set():
                        start_signal.set()

    @abstractmethod
    async def _get_msgs(self, *args: Any) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def channel_name(self) -> str:
        raise NotImplementedError()

    async def close(self) -> None:
        await super().close()

        if self.task is not None and not self.task.done():
            self.task.cancel()
        self.task = None

    @staticmethod
    def build_log_context(
        message: Optional["BrokerStreamMessage[Any]"],
        channel: str = "",
    ) -> Dict[str, str]:
        return {
            "channel": channel,
            "message_id": getattr(message, "message_id", ""),
        }

    def get_log_context(
        self,
        message: Optional["BrokerStreamMessage[Any]"],
    ) -> Dict[str, str]:
        return self.build_log_context(
            message=message,
            channel=self.channel_name,
        )


class ChannelHandler(BaseRedisHandler[PubSubMessage]):
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
            Iterable["BrokerMiddleware[PubSubMessage]"],
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

    def add_call(
        self,
        *,
        filter: "Filter[BrokerStreamMessage[PubSubMessage]]",
        parser: Optional["CustomParser[PubSubMessage]"],
        decoder: Optional["CustomDecoder[BrokerStreamMessage[PubSubMessage]]"],
        middlewares: Iterable["SubscriberMiddleware"],
        dependencies: Sequence["Depends"],
        **wrap_kwargs: Any,
    ) -> "WrapperProtocol[PubSubMessage]":
        return super(BaseRedisHandler, self).add_call(
            parser_=resolve_custom_func(parser, RedisPubSubParser.parse_message),
            decoder_=resolve_custom_func(decoder, RedisPubSubParser.decode_message),
            filter_=filter,
            middlewares_=middlewares,
            dependencies_=dependencies,
            **wrap_kwargs,
        )

    @override
    async def start(  # type: ignore[override]
        self,
        client: "Redis[bytes]",
        *,
        producer: Optional["PublisherProtocol"],
    ) -> None:
        self.subscription = psub = client.pubsub()

        if self.channel.pattern:
            await psub.psubscribe(self.channel.name)
        else:
            await psub.subscribe(self.channel.name)

        await super().start(psub, producer=producer)

    async def close(self) -> None:
        if self.subscription is not None:
            await self.subscription.unsubscribe()
            await self.subscription.aclose()  # type: ignore[attr-defined]
            self.subscription = None

        await super().close()

    async def _get_msgs(self, psub: RPubSub) -> None:
        raw_msg = await psub.get_message(
            ignore_subscribe_messages=True,
            timeout=self.channel.polling_interval,
        )

        if raw_msg:
            msg = PubSubMessage(
                type=raw_msg["type"],
                data=raw_msg["data"],
                channel=raw_msg["channel"].decode(),
                pattern=raw_msg["pattern"],
            )
            await self.consume(msg)


class _ListHandlerMixin(BaseRedisHandler[MsgType]):
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
            Iterable["BrokerMiddleware[MsgType]"],
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

    async def _consume(
        self, client: "Redis[bytes]", *, start_signal: anyio.Event
    ) -> None:
        start_signal.set()
        await super()._consume(client, start_signal=start_signal)

    @override
    async def start(  # type: ignore[override]
        self,
        client: "Redis[bytes]",
        *,
        producer: Optional["PublisherProtocol"],
    ) -> None:
        await super().start(client, producer=producer)


class ListHandler(_ListHandlerMixin[bytes]):
    def add_call(
        self,
        *,
        filter: "Filter[BrokerStreamMessage[ListMessage]]",
        parser: Optional["CustomParser[ListMessage]"],
        decoder: Optional["CustomDecoder[BrokerStreamMessage[ListMessage]]"],
        middlewares: Iterable["SubscriberMiddleware"],
        dependencies: Sequence["Depends"],
        **wrap_kwargs: Any,
    ) -> "WrapperProtocol[ListMessage]":
        return super(BaseRedisHandler, self).add_call(
            parser_=resolve_custom_func(parser, RedisListParser.parse_message),
            decoder_=resolve_custom_func(decoder, RedisListParser.decode_message),
            filter_=filter,
            middlewares_=middlewares,
            dependencies_=dependencies,
            **wrap_kwargs,
        )

    async def _get_msgs(self, client: "Redis[bytes]") -> None:
        raw_msg = await client.lpop(name=self.channel_name)

        if raw_msg:
            message = ListMessage(
                type="list",
                data=raw_msg,
                channel=self.channel_name,
            )

            await self.consume(message)

        else:
            await anyio.sleep(self.list_sub.polling_interval)


class BatchListHandler(_ListHandlerMixin[BatchListMessage]):
    def add_call(
        self,
        *,
        filter: "Filter[BrokerStreamMessage[BatchListMessage]]",
        parser: Optional["CustomParser[BatchListMessage]"],
        decoder: Optional["CustomDecoder[BrokerStreamMessage[BatchListMessage]]"],
        middlewares: Iterable["SubscriberMiddleware"],
        dependencies: Sequence["Depends"],
        **wrap_kwargs: Any,
    ) -> "WrapperProtocol[BatchListMessage]":
        return super(BaseRedisHandler, self).add_call(
            parser_=resolve_custom_func(parser, RedisBatchListParser.parse_message),
            decoder_=resolve_custom_func(decoder, RedisBatchListParser.decode_message),
            filter_=filter,
            middlewares_=middlewares,
            dependencies_=dependencies,
            **wrap_kwargs,
        )

    async def _get_msgs(self, client: "Redis[bytes]") -> None:
        raw_msgs = await client.lpop(
            name=self.channel_name,
            count=self.list_sub.max_records,
        )

        if raw_msgs:
            msg = BatchListMessage(
                type="batch",
                channel=self.channel_name,
                data=raw_msgs,
            )

            await self.consume(msg)

        else:
            await anyio.sleep(self.list_sub.polling_interval)

    async def _consume(self, psub: RPubSub, *, start_signal: anyio.Event) -> None:
        start_signal.set()
        await super()._consume(psub, start_signal=start_signal)


class _StreamHandlerMixin(BaseRedisHandler[MsgType]):
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
            Iterable["BrokerMiddleware[MsgType]"],
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
        self.last_id = getattr(stream, "last_id", "$")

    @cached_property
    def channel_name(self) -> str:
        return self.stream_sub.name

    @override
    async def start(  # type: ignore[override]
        self,
        client: "Redis[bytes]",
        *,
        producer: Optional["PublisherProtocol"],
    ) -> None:
        self.extra_watcher_options.update(redis=client, group=self.stream_sub.group)

        stream = self.stream_sub

        if stream.group and stream.consumer:
            try:
                await client.xgroup_create(
                    name=stream.name,
                    id=self.last_id,
                    groupname=stream.group,
                    mkstream=True,
                )
            except ResponseError as e:
                if "already exists" not in str(e):
                    raise e

            read = lambda _: client.xreadgroup(  # noqa: E731
                groupname=stream.group,
                consumername=stream.consumer,
                streams={stream.name: ">"},
                count=stream.max_records,
                block=stream.polling_interval,
                noack=stream.no_ack,
            )

        else:
            read = lambda last_id: client.xread(  # noqa: E731
                {stream.name: last_id},
                block=stream.polling_interval,
                count=stream.max_records,
            )

        await super().start(read, producer=producer)


class StreamHandler(_StreamHandlerMixin[StreamMessage]):
    def add_call(
        self,
        *,
        filter: "Filter[BrokerStreamMessage[StreamMessage]]",
        parser: Optional["CustomParser[StreamMessage]"],
        decoder: Optional["CustomDecoder[BrokerStreamMessage[StreamMessage]]"],
        middlewares: Iterable["SubscriberMiddleware"],
        dependencies: Sequence["Depends"],
        **wrap_kwargs: Any,
    ) -> "WrapperProtocol[StreamMessage]":
        return super(BaseRedisHandler, self).add_call(
            parser_=resolve_custom_func(parser, RedisStreamParser.parse_message),
            decoder_=resolve_custom_func(decoder, RedisStreamParser.decode_message),
            filter_=filter,
            middlewares_=middlewares,
            dependencies_=dependencies,
            **wrap_kwargs,
        )

    async def _get_msgs(
        self,
        read: Callable[
            [str],
            Awaitable[
                Tuple[Tuple[bytes, Tuple[Tuple[bytes, Dict[Any, Any]], ...]], ...],
            ],
        ],
    ) -> None:
        for stream_name, msgs in await read(self.last_id):
            if msgs:
                self.last_id = msgs[-1][0].decode()

                for message_id, raw_msg in msgs:
                    msg = StreamMessage(
                        type="stream",
                        channel=stream_name.decode(),
                        message_ids=[message_id],
                        data=raw_msg,
                    )

                    await self.consume(msg)


class BatchStreamHandler(_StreamHandlerMixin[BatchStreamMessage]):
    def add_call(
        self,
        *,
        filter: "Filter[BrokerStreamMessage[BatchStreamMessage]]",
        parser: Optional["CustomParser[BatchStreamMessage]"],
        decoder: Optional["CustomDecoder[BrokerStreamMessage[BatchStreamMessage]]"],
        middlewares: Iterable["SubscriberMiddleware"],
        dependencies: Sequence["Depends"],
        **wrap_kwargs: Any,
    ) -> "WrapperProtocol[BatchStreamMessage]":
        return super(BaseRedisHandler, self).add_call(
            parser_=resolve_custom_func(parser, RedisBatchStreamParser.parse_message),
            decoder_=resolve_custom_func(
                decoder, RedisBatchStreamParser.decode_message
            ),
            filter_=filter,
            middlewares_=middlewares,
            dependencies_=dependencies,
            **wrap_kwargs,
        )

    async def _get_msgs(
        self,
        read: Callable[
            [str],
            Awaitable[
                Tuple[Tuple[bytes, Tuple[Tuple[bytes, Dict[Any, Any]], ...]], ...],
            ],
        ],
    ) -> None:
        for stream_name, msgs in await read(self.last_id):
            if msgs:
                self.last_id = msgs[-1][0].decode()

                data, ids = [], []
                for message_id, msg in msgs:
                    data.append(msg)
                    ids.append(message_id)

                msg = BatchStreamMessage(
                    type="stream",
                    channel=stream_name.decode(),
                    data=data,
                    message_ids=ids,
                )

                await self.consume(msg)
