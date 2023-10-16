from functools import partial, wraps
from types import TracebackType
from typing import Any, Awaitable, Callable, Dict, Optional, Sequence, Type

from fast_depends.dependencies import Depends
from redis.asyncio.client import Redis
from redis.asyncio.connection import ConnectionPool, parse_url

from faststream._compat import override
from faststream.broker.core.asyncronous import BrokerAsyncUsecase, default_filter
from faststream.broker.message import StreamMessage
from faststream.broker.middlewares import BaseMiddleware
from faststream.broker.push_back_watcher import BaseWatcher, WatcherContext
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
from faststream.redis.asyncapi import Handler, Publisher
from faststream.redis.message import PubSubMessage, RedisMessage
from faststream.redis.producer import RedisFastProducer
from faststream.redis.shared.logging import RedisLoggingMixin
from faststream.types import AnyDict, DecodedMessage
from faststream.utils.context.main import context

Channel = str


class RedisBroker(
    RedisLoggingMixin,
    BrokerAsyncUsecase[PubSubMessage, Redis],
):
    handlers: Dict[Channel, Handler]  # type: ignore[assignment]
    _publishers: Dict[Channel, Publisher]  # type: ignore[assignment]

    _producer: Optional[RedisFastProducer]

    def __init__(
        self,
        url: str = "redis://localhost:6379",
        polling_interval: float = 1.0,
        *,
        protocol: str = "redis",
        protocol_version: Optional[str] = "custom",
        **kwargs: Any,
    ) -> None:
        self.global_polling_interval = polling_interval
        self._producer = None

        super().__init__(
            url=url,
            protocol=protocol,
            protocol_version=protocol_version,
            **kwargs,
        )

    async def connect(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Redis:
        connection = await super().connect(*args, **kwargs)
        for p in self._publishers.values():
            p._producer = self._producer
        return connection

    async def _connect(
        self,
        url: str,
        **kwargs: Any,
    ) -> Redis:
        url_options = parse_url(url)
        url_options.update(kwargs)
        pool = ConnectionPool(**url_options)

        client = Redis(connection_pool=pool)
        self._producer = RedisFastProducer(
            connection=client,
            parser=self._global_parser,
            decoder=self._global_parser,
        )
        return client

    async def _close(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exec_tb: Optional[TracebackType] = None,
    ) -> None:
        if self._connection is not None:
            await self._connection.close()

        await super()._close(exc_type, exc_val, exec_tb)

    async def start(self) -> None:
        context.set_local(
            "log_context",
            self._get_log_context(None, ""),
        )

        await super().start()
        assert self._connection, "Broker should be started already"  # nosec B101

        for handler in self.handlers.values():
            c = self._get_log_context(None, handler.channel)
            self._log(f"`{handler.call_name}` waiting for messages", extra=c)
            await handler.start(self._connection)

    def _process_message(
        self,
        func: Callable[
            [StreamMessage[Any]],
            Awaitable[T_HandlerReturn],
        ],
        watcher: BaseWatcher,
    ) -> Callable[[StreamMessage[Any]], Awaitable[WrappedReturn[T_HandlerReturn]],]:
        @wraps(func)
        async def process_wrapper(
            message: StreamMessage[Any],
        ) -> WrappedReturn[T_HandlerReturn]:
            async with WatcherContext(watcher, message):
                r = await self._execute_handler(func, message)

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
        channel: Channel,
        pattern: bool = False,
        polling_interval: Optional[float] = None,
        # broker arguments
        dependencies: Sequence[Depends] = (),
        parser: Optional[CustomParser[PubSubMessage, RedisMessage]] = None,
        decoder: Optional[CustomDecoder[RedisMessage]] = None,
        middlewares: Optional[
            Sequence[Callable[[PubSubMessage], BaseMiddleware]]
        ] = None,
        filter: Filter[RedisMessage] = default_filter,
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        **original_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[Any, P_HandlerParams, T_HandlerReturn],
    ]:
        self._setup_log_context(channel=channel)
        super().subscriber()

        key = Handler.get_routing_hash(channel)
        handler = self.handlers[key] = self.handlers.get(
            key,
            Handler(
                channel=channel,
                pattern=pattern,
                polling_interval=(
                    polling_interval
                    if polling_interval is not None
                    else self.global_polling_interval
                ),
                title=title,
                description=description,
                log_context_builder=partial(
                    self._get_log_context,
                    channel=channel,
                ),
            ),
        )

        def consumer_wrapper(
            func: Callable[P_HandlerParams, T_HandlerReturn],
        ) -> HandlerCallWrapper[PubSubMessage, P_HandlerParams, T_HandlerReturn,]:
            handler_call, dependant = self._wrap_handler(
                func,
                extra_dependencies=dependencies,
                **original_kwargs,
            )

            handler.add_call(
                handler=handler_call,
                filter=filter,
                middlewares=middlewares,
                parser=parser or self._global_parser,
                decoder=decoder or self._global_decoder,
                dependant=dependant,
            )

            return handler_call

        return consumer_wrapper

    @override
    def publisher(  # type: ignore[override]
        self,
        channel: str,
        headers: Optional[AnyDict] = None,
        reply_to: str = "",
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        schema: Optional[Any] = None,
    ):
        publisher = self._publishers.get(
            channel,
            Publisher(
                channel=channel,
                headers=headers,
                reply_to=reply_to,
                # AsyncAPI
                title=title,
                _description=description,
                _schema=schema,
            ),
        )
        super().publisher(channel, publisher)
        return publisher

    @override
    async def publish(  # type: ignore[override]
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Optional[DecodedMessage]:
        return await self._producer.publish(*args, **kwargs)
