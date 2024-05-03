import asyncio
from abc import ABC, abstractmethod
from contextlib import suppress
from copy import deepcopy
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
)

import anyio
from redis.asyncio.client import PubSub as RPubSub
from redis.asyncio.client import Redis
from redis.exceptions import ResponseError
from typing_extensions import TypeAlias, override

from faststream.broker.publisher.fake import FakePublisher
from faststream.broker.subscriber.usecase import SubscriberUsecase
from faststream.redis.message import (
    BatchListMessage,
    BatchStreamMessage,
    DefaultListMessage,
    DefaultStreamMessage,
    PubSubMessage,
    UnifyRedisDict,
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

    from faststream.broker.message import StreamMessage as BrokerStreamMessage
    from faststream.broker.publisher.proto import ProducerProto
    from faststream.broker.types import (
        AsyncCallable,
        BrokerMiddleware,
        CustomCallable,
    )
    from faststream.types import AnyDict, Decorator, LoggerProto


TopicName: TypeAlias = bytes
Offset: TypeAlias = bytes


class LogicSubscriber(ABC, SubscriberUsecase[UnifyRedisDict]):
    """A class to represent a Redis handler."""

    _client: Optional["Redis[bytes]"]

    def __init__(
        self,
        *,
        default_parser: "AsyncCallable",
        default_decoder: "AsyncCallable",
        # Subscriber args
        no_ack: bool,
        retry: bool,
        broker_dependencies: Iterable["Depends"],
        broker_middlewares: Iterable["BrokerMiddleware[UnifyRedisDict]"],
        # AsyncAPI args
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        super().__init__(
            default_parser=default_parser,
            default_decoder=default_decoder,
            # Propagated options
            no_ack=no_ack,
            retry=retry,
            broker_middlewares=broker_middlewares,
            broker_dependencies=broker_dependencies,
            # AsyncAPI
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

        self._client = None
        self.task: Optional["asyncio.Task[None]"] = None

    @override
    def setup(  # type: ignore[override]
        self,
        *,
        connection: Optional["Redis[bytes]"],
        # basic args
        logger: Optional["LoggerProto"],
        producer: Optional["ProducerProto"],
        graceful_timeout: Optional[float],
        extra_context: "AnyDict",
        # broker options
        broker_parser: Optional["CustomCallable"],
        broker_decoder: Optional["CustomCallable"],
        # dependant args
        apply_types: bool,
        is_validate: bool,
        _get_dependant: Optional[Callable[..., Any]],
        _call_decorators: Iterable["Decorator"],
    ) -> None:
        self._client = connection

        super().setup(
            logger=logger,
            producer=producer,
            graceful_timeout=graceful_timeout,
            extra_context=extra_context,
            broker_parser=broker_parser,
            broker_decoder=broker_decoder,
            apply_types=apply_types,
            is_validate=is_validate,
            _get_dependant=_get_dependant,
            _call_decorators=_call_decorators,
        )

    def _make_response_publisher(
        self, message: "BrokerStreamMessage[UnifyRedisDict]"
    ) -> Sequence[FakePublisher]:
        if not message.reply_to or self._producer is None:
            return ()

        return (
            FakePublisher(
                self._producer.publish,
                publish_kwargs={
                    "channel": message.reply_to,
                },
            ),
        )

    @override
    async def start(  # type: ignore[override]
        self,
        *args: Any,
    ) -> None:
        await super().start()

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


class ChannelSubscriber(LogicSubscriber):
    subscription: Optional[RPubSub]

    def __init__(
        self,
        *,
        channel: "PubSub",
        # Subscriber args
        no_ack: bool,
        retry: bool,
        broker_dependencies: Iterable["Depends"],
        broker_middlewares: Iterable["BrokerMiddleware[UnifyRedisDict]"],
        # AsyncAPI args
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        parser = RedisPubSubParser(pattern=channel.path_regex)
        super().__init__(
            default_parser=parser.parse_message,
            default_decoder=parser.decode_message,
            # Propagated options
            no_ack=no_ack,
            retry=retry,
            broker_middlewares=broker_middlewares,
            broker_dependencies=broker_dependencies,
            # AsyncAPI
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

        self.channel = channel
        self.subscription = None

    def __hash__(self) -> int:
        return hash(self.channel)

    def get_log_context(
        self,
        message: Optional["BrokerStreamMessage[Any]"],
    ) -> Dict[str, str]:
        return self.build_log_context(
            message=message,
            channel=self.channel.name,
        )

    @override
    async def start(self) -> None:
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
            await self.consume(msg)  # type: ignore[arg-type]

    def add_prefix(self, prefix: str) -> None:
        new_ch = deepcopy(self.channel)
        new_ch.name = "".join((prefix, new_ch.name))
        self.channel = new_ch


class _ListHandlerMixin(LogicSubscriber):
    def __init__(
        self,
        *,
        list: ListSub,
        default_parser: "AsyncCallable",
        default_decoder: "AsyncCallable",
        # Subscriber args
        no_ack: bool,
        retry: bool,
        broker_dependencies: Iterable["Depends"],
        broker_middlewares: Iterable["BrokerMiddleware[UnifyRedisDict]"],
        # AsyncAPI args
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        super().__init__(
            default_parser=default_parser,
            default_decoder=default_decoder,
            # Propagated options
            no_ack=no_ack,
            retry=retry,
            broker_middlewares=broker_middlewares,
            broker_dependencies=broker_dependencies,
            # AsyncAPI
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

        self.list_sub = list

    def __hash__(self) -> int:
        return hash(self.list_sub)

    def get_log_context(
        self,
        message: Optional["BrokerStreamMessage[Any]"],
    ) -> Dict[str, str]:
        return self.build_log_context(
            message=message,
            channel=self.list_sub.name,
        )

    @override
    async def _consume(  # type: ignore[override]
        self,
        client: "Redis[bytes]",
        *,
        start_signal: "anyio.Event",
    ) -> None:
        start_signal.set()
        await super()._consume(client, start_signal=start_signal)

    @override
    async def start(self) -> None:
        assert self._client, "You should setup subscriber at first."  # nosec B101
        await super().start(self._client)

    def add_prefix(self, prefix: str) -> None:
        new_list = deepcopy(self.list_sub)
        new_list.name = "".join((prefix, new_list.name))
        self.list_sub = new_list


class ListSubscriber(_ListHandlerMixin):
    def __init__(
        self,
        *,
        list: ListSub,
        # Subscriber args
        no_ack: bool,
        retry: bool,
        broker_dependencies: Iterable["Depends"],
        broker_middlewares: Iterable["BrokerMiddleware[UnifyRedisDict]"],
        # AsyncAPI args
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        parser = RedisListParser()
        super().__init__(
            list=list,
            default_parser=parser.parse_message,
            default_decoder=parser.decode_message,
            # Propagated options
            no_ack=no_ack,
            retry=retry,
            broker_middlewares=broker_middlewares,
            broker_dependencies=broker_dependencies,
            # AsyncAPI
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

    async def _get_msgs(self, client: "Redis[bytes]") -> None:
        raw_msg = await client.lpop(name=self.list_sub.name)

        if raw_msg:
            message = DefaultListMessage(
                type="list",
                data=raw_msg,
                channel=self.list_sub.name,
            )

            await self.consume(message)  # type: ignore[arg-type]

        else:
            await anyio.sleep(self.list_sub.polling_interval)


class BatchListSubscriber(_ListHandlerMixin):
    def __init__(
        self,
        *,
        list: ListSub,
        # Subscriber args
        no_ack: bool,
        retry: bool,
        broker_dependencies: Iterable["Depends"],
        broker_middlewares: Iterable["BrokerMiddleware[UnifyRedisDict]"],
        # AsyncAPI args
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        parser = RedisBatchListParser()
        super().__init__(
            list=list,
            default_parser=parser.parse_message,
            default_decoder=parser.decode_message,
            # Propagated options
            no_ack=no_ack,
            retry=retry,
            broker_middlewares=broker_middlewares,
            broker_dependencies=broker_dependencies,
            # AsyncAPI
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

    async def _get_msgs(self, client: "Redis[bytes]") -> None:
        raw_msgs = await client.lpop(
            name=self.list_sub.name,
            count=self.list_sub.max_records,
        )

        if raw_msgs:
            msg = BatchListMessage(
                type="blist",
                channel=self.list_sub.name,
                data=raw_msgs,
            )

            await self.consume(msg)  # type: ignore[arg-type]

        else:
            await anyio.sleep(self.list_sub.polling_interval)


class _StreamHandlerMixin(LogicSubscriber):
    def __init__(
        self,
        *,
        stream: StreamSub,
        default_parser: "AsyncCallable",
        default_decoder: "AsyncCallable",
        # Subscriber args
        no_ack: bool,
        retry: bool,
        broker_dependencies: Iterable["Depends"],
        broker_middlewares: Iterable["BrokerMiddleware[UnifyRedisDict]"],
        # AsyncAPI args
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        super().__init__(
            default_parser=default_parser,
            default_decoder=default_decoder,
            # Propagated options
            no_ack=no_ack,
            retry=retry,
            broker_middlewares=broker_middlewares,
            broker_dependencies=broker_dependencies,
            # AsyncAPI
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

        self.stream_sub = stream
        self.last_id = stream.last_id

    def __hash__(self) -> int:
        return hash(self.stream_sub)

    def get_log_context(
        self,
        message: Optional["BrokerStreamMessage[Any]"],
    ) -> Dict[str, str]:
        return self.build_log_context(
            message=message,
            channel=self.stream_sub.name,
        )

    @override
    async def start(self) -> None:
        assert self._client, "You should setup subscriber at first."  # nosec B101
        client = self._client

        self.extra_watcher_options.update(
            redis=client,
            group=self.stream_sub.group,
        )

        stream = self.stream_sub

        read: Callable[
            [str],
            Awaitable[
                Tuple[
                    Tuple[
                        TopicName,
                        Tuple[
                            Tuple[
                                Offset,
                                Dict[bytes, bytes],
                            ],
                            ...,
                        ],
                    ],
                    ...,
                ],
            ],
        ]

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

            def read(
                _: str,
            ) -> Awaitable[
                Tuple[
                    Tuple[
                        TopicName,
                        Tuple[
                            Tuple[
                                Offset,
                                Dict[bytes, bytes],
                            ],
                            ...,
                        ],
                    ],
                    ...,
                ],
            ]:
                return client.xreadgroup(
                    groupname=stream.group,
                    consumername=stream.consumer,
                    streams={stream.name: ">"},
                    count=stream.max_records,
                    block=stream.polling_interval,
                    noack=stream.no_ack,
                )

        else:

            def read(
                last_id: str,
            ) -> Awaitable[
                Tuple[
                    Tuple[
                        TopicName,
                        Tuple[
                            Tuple[
                                Offset,
                                Dict[bytes, bytes],
                            ],
                            ...,
                        ],
                    ],
                    ...,
                ],
            ]:
                return client.xread(
                    {stream.name: last_id},
                    block=stream.polling_interval,
                    count=stream.max_records,
                )

        await super().start(read)

    def add_prefix(self, prefix: str) -> None:
        new_stream = deepcopy(self.stream_sub)
        new_stream.name = "".join((prefix, new_stream.name))
        self.stream_sub = new_stream


class StreamSubscriber(_StreamHandlerMixin):
    def __init__(
        self,
        *,
        stream: StreamSub,
        # Subscriber args
        no_ack: bool,
        retry: bool,
        broker_dependencies: Iterable["Depends"],
        broker_middlewares: Iterable["BrokerMiddleware[UnifyRedisDict]"],
        # AsyncAPI args
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        parser = RedisStreamParser()
        super().__init__(
            stream=stream,
            default_parser=parser.parse_message,
            default_decoder=parser.decode_message,
            # Propagated options
            no_ack=no_ack,
            retry=retry,
            broker_middlewares=broker_middlewares,
            broker_dependencies=broker_dependencies,
            # AsyncAPI
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

    async def _get_msgs(
        self,
        read: Callable[
            [str],
            Awaitable[
                Tuple[
                    Tuple[
                        TopicName,
                        Tuple[
                            Tuple[
                                Offset,
                                Dict[bytes, bytes],
                            ],
                            ...,
                        ],
                    ],
                    ...,
                ],
            ],
        ],
    ) -> None:
        for stream_name, msgs in await read(self.last_id):
            if msgs:
                self.last_id = msgs[-1][0].decode()

                for message_id, raw_msg in msgs:
                    msg = DefaultStreamMessage(
                        type="stream",
                        channel=stream_name.decode(),
                        message_ids=[message_id],
                        data=raw_msg,
                    )

                    await self.consume(msg)  # type: ignore[arg-type]


class BatchStreamSubscriber(_StreamHandlerMixin):
    def __init__(
        self,
        *,
        stream: StreamSub,
        # Subscriber args
        no_ack: bool,
        retry: bool,
        broker_dependencies: Iterable["Depends"],
        broker_middlewares: Iterable["BrokerMiddleware[UnifyRedisDict]"],
        # AsyncAPI args
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        parser = RedisBatchStreamParser()
        super().__init__(
            stream=stream,
            default_parser=parser.parse_message,
            default_decoder=parser.decode_message,
            # Propagated options
            no_ack=no_ack,
            retry=retry,
            broker_middlewares=broker_middlewares,
            broker_dependencies=broker_dependencies,
            # AsyncAPI
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

    async def _get_msgs(
        self,
        read: Callable[
            [str],
            Awaitable[
                Tuple[Tuple[bytes, Tuple[Tuple[bytes, Dict[bytes, bytes]], ...]], ...],
            ],
        ],
    ) -> None:
        for stream_name, msgs in await read(self.last_id):
            if msgs:
                self.last_id = msgs[-1][0].decode()

                data: List[Dict[bytes, bytes]] = []
                ids: List[bytes] = []
                for message_id, i in msgs:
                    data.append(i)
                    ids.append(message_id)

                msg = BatchStreamMessage(
                    type="bstream",
                    channel=stream_name.decode(),
                    data=data,
                    message_ids=ids,
                )

                await self.consume(msg)  # type: ignore[arg-type]
