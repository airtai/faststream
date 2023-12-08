from functools import partial, wraps
from types import TracebackType
from typing import (
    Any,
    AsyncContextManager,
    Awaitable,
    Callable,
    Dict,
    Optional,
    Sequence,
    Type,
    Union,
)
from urllib.parse import urlparse

from fast_depends.dependencies import Depends
from redis.asyncio.client import Redis
from redis.asyncio.connection import ConnectionPool, parse_url
from redis.exceptions import ResponseError

from faststream._compat import TypeAlias, override
from faststream.broker.core.asyncronous import BrokerAsyncUsecase, default_filter
from faststream.broker.message import StreamMessage
from faststream.broker.middlewares import BaseMiddleware
from faststream.broker.types import (
    AsyncPublisherProtocol,
    CustomDecoder,
    CustomParser,
    Filter,
    P_HandlerParams,
    T_HandlerReturn,
    WrappedReturn,
)
from faststream.broker.wrapper import FakePublisher, HandlerCallWrapper
from faststream.exceptions import NOT_CONNECTED_YET
from faststream.redis.asyncapi import Handler, Publisher
from faststream.redis.message import AnyRedisDict, RedisMessage
from faststream.redis.producer import RedisFastProducer
from faststream.redis.schemas import INCORRECT_SETUP_MSG, ListSub, PubSub, StreamSub
from faststream.redis.security import parse_security
from faststream.redis.shared.logging import RedisLoggingMixin
from faststream.security import BaseSecurity
from faststream.types import AnyDict, DecodedMessage
from faststream.utils.context.main import context

Channel: TypeAlias = str


class RedisBroker(
    RedisLoggingMixin,
    BrokerAsyncUsecase[AnyRedisDict, "Redis[bytes]"],
):
    url: str
    handlers: Dict[int, Handler]
    _publishers: Dict[int, Publisher]

    _producer: Optional[RedisFastProducer]

    def __init__(
        self,
        url: str = "redis://localhost:6379",
        polling_interval: Optional[float] = None,
        *,
        protocol: Optional[str] = None,
        protocol_version: Optional[str] = "custom",
        security: Optional[BaseSecurity] = None,
        **kwargs: Any,
    ) -> None:
        self.global_polling_interval = polling_interval
        self._producer = None

        super().__init__(
            url=url,
            protocol_version=protocol_version,
            security=security,
            **kwargs,
        )

        url_kwargs = urlparse(self.url)
        self.protocol = protocol or url_kwargs.scheme

    async def connect(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> "Redis[bytes]":
        connection = await super().connect(*args, **kwargs)
        for p in self._publishers.values():
            p._producer = self._producer
        return connection

    @override
    async def _connect(  # type: ignore[override]
        self,
        url: str,
        **kwargs: Any,
    ) -> "Redis[bytes]":
        url_options: AnyDict = parse_url(url)
        url_options.update(kwargs)
        url_options.update(parse_security(self.security))
        pool = ConnectionPool(**url_options)

        client = Redis.from_pool(pool)
        self._producer = RedisFastProducer(
            connection=client,
            parser=self._global_parser,  # type: ignore[arg-type]
            decoder=self._global_parser,  # type: ignore[arg-type]
        )
        return client

    async def _close(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exec_tb: Optional[TracebackType] = None,
    ) -> None:
        if self._connection is not None:
            await self._connection.aclose()  # type: ignore[attr-defined]

        await super()._close(exc_type, exc_val, exec_tb)

    async def start(self) -> None:
        context.set_global(
            "default_log_context",
            self._get_log_context(None, ""),
        )

        await super().start()
        assert self._connection, NOT_CONNECTED_YET  # nosec B101

        for handler in self.handlers.values():
            if (stream := handler.stream_sub) is not None and stream.group:
                try:
                    await self._connection.xgroup_create(
                        name=stream.name,
                        groupname=stream.group,
                        mkstream=True,
                    )
                except ResponseError as e:
                    if "already exists" not in str(e):
                        raise e

            c = self._get_log_context(None, handler.channel_name)
            self._log(f"`{handler.call_name}` waiting for messages", extra=c)
            await handler.start(self._connection)

    def _process_message(
        self,
        func: Callable[[StreamMessage[Any]], Awaitable[T_HandlerReturn]],
        watcher: Callable[..., AsyncContextManager[None]],
        **kwargs: Any,
    ) -> Callable[[StreamMessage[Any]], Awaitable[WrappedReturn[T_HandlerReturn]],]:
        @wraps(func)
        async def process_wrapper(
            message: StreamMessage[Any],
        ) -> WrappedReturn[T_HandlerReturn]:
            async with watcher(
                message,
                redis=self._connection,
            ):
                r = await func(message)

                pub_response: Optional[AsyncPublisherProtocol]
                if message.reply_to:
                    pub_response = FakePublisher(
                        partial(self.publish, channel=message.reply_to)
                    )
                else:
                    pub_response = None

                return r, pub_response

        return process_wrapper

    @override
    def subscriber(  # type: ignore[override]
        self,
        channel: Union[Channel, PubSub, None] = None,
        *,
        list: Union[Channel, ListSub, None] = None,
        stream: Union[Channel, StreamSub, None] = None,
        # broker arguments
        dependencies: Sequence[Depends] = (),
        parser: Optional[CustomParser[AnyRedisDict, RedisMessage]] = None,
        decoder: Optional[CustomDecoder[RedisMessage]] = None,
        middlewares: Optional[
            Sequence[Callable[[AnyRedisDict], BaseMiddleware]]
        ] = None,
        filter: Filter[RedisMessage] = default_filter,
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        include_in_schema: bool = True,
        **original_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[Any, P_HandlerParams, T_HandlerReturn],
    ]:
        channel = PubSub.validate(channel)
        list = ListSub.validate(list)
        stream = StreamSub.validate(stream)

        if (any_of := channel or list or stream) is None:
            raise ValueError(
                "You should specify `channel`, `list`, `stream` subscriber type"
            )

        if all((channel, list)):
            raise ValueError("You can't use `PubSub` and `ListSub` both")
        elif all((channel, stream)):
            raise ValueError("You can't use `PubSub` and `StreamSub` both")
        elif all((list, stream)):
            raise ValueError("You can't use `ListSub` and `StreamSub` both")

        self._setup_log_context(channel=any_of.name)
        super().subscriber()

        key = Handler.get_routing_hash(any_of)
        handler = self.handlers[key] = self.handlers.get(
            key,
            Handler(  # type: ignore[abstract]
                log_context_builder=partial(
                    self._get_log_context,
                    channel=any_of.name,
                ),
                # Redis
                channel=channel,
                list=list,
                stream=stream,
                # AsyncAPI
                title=title,
                description=description,
                include_in_schema=include_in_schema,
            ),
        )

        def consumer_wrapper(
            func: Callable[P_HandlerParams, T_HandlerReturn],
        ) -> HandlerCallWrapper[AnyRedisDict, P_HandlerParams, T_HandlerReturn,]:
            handler_call, dependant = self._wrap_handler(
                func,
                extra_dependencies=dependencies,
                **original_kwargs,
            )

            handler.add_call(
                handler=handler_call,
                filter=filter,
                middlewares=middlewares,
                parser=parser or self._global_parser,  # type: ignore[arg-type]
                decoder=decoder or self._global_decoder,  # type: ignore[arg-type]
                dependant=dependant,
            )

            return handler_call

        return consumer_wrapper

    @override
    def publisher(  # type: ignore[override]
        self,
        channel: Union[Channel, PubSub, None] = None,
        list: Union[Channel, ListSub, None] = None,
        stream: Union[Channel, StreamSub, None] = None,
        headers: Optional[AnyDict] = None,
        reply_to: str = "",
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        schema: Optional[Any] = None,
        include_in_schema: bool = True,
    ) -> Publisher:
        channel = PubSub.validate(channel)
        list = ListSub.validate(list)
        stream = StreamSub.validate(stream)

        any_of = channel or list or stream
        if any_of is None:
            raise ValueError(INCORRECT_SETUP_MSG)

        key = Handler.get_routing_hash(any_of)
        publisher = self._publishers.get(
            key,
            Publisher(
                channel=channel,
                list=list,
                stream=stream,
                headers=headers,
                reply_to=reply_to,
                # AsyncAPI
                title=title,
                _description=description,
                _schema=schema,
                include_in_schema=include_in_schema,
            ),
        )
        super().publisher(key, publisher)
        if self._producer is not None:
            publisher._producer = self._producer
        return publisher

    @override
    async def publish(  # type: ignore[override]
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Optional[DecodedMessage]:
        assert self._producer, NOT_CONNECTED_YET  # nosec B101
        return await self._producer.publish(*args, **kwargs)

    async def publish_batch(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        assert self._producer, NOT_CONNECTED_YET  # nosec B101
        return await self._producer.publish_batch(*args, **kwargs)
