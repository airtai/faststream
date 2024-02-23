from contextlib import AsyncExitStack
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    Optional,
    Sequence,
    Type,
    Union,
)
from urllib.parse import urlparse

from fast_depends.dependencies import Depends
from redis.asyncio.client import Redis
from redis.asyncio.connection import ConnectionPool, parse_url
from typing_extensions import TypeAlias, override

from faststream.broker.core.broker import BrokerUsecase, default_filter
from faststream.broker.core.call_wrapper import HandlerCallWrapper
from faststream.broker.types import (
    CustomDecoder,
    CustomParser,
    Filter,
    P_HandlerParams,
    PublisherMiddleware,
    SubscriberMiddleware,
    T_HandlerReturn,
)
from faststream.broker.utils import get_watcher_context
from faststream.exceptions import NOT_CONNECTED_YET
from faststream.redis.asyncapi import Handler, Publisher
from faststream.redis.broker.logging import RedisLoggingMixin
from faststream.redis.producer import RedisFastProducer
from faststream.redis.schemas import INCORRECT_SETUP_MSG, ListSub, PubSub, StreamSub
from faststream.redis.security import parse_security
from faststream.security import BaseSecurity
from faststream.types import AnyDict, DecodedMessage, SendableMessage

Channel: TypeAlias = str


class RedisBroker(
    RedisLoggingMixin,
    BrokerUsecase["AnyRedisDict", "Redis[bytes]"],
):
    """Redis broker."""

    url: str
    handlers: Dict[int, Handler]
    _publishers: Dict[int, Publisher]

    _producer: Optional[RedisFastProducer]

    def __init__(
        self,
        url: str = "redis://localhost:6379",
        polling_interval: Optional[float] = None,
        *,
        security: Optional[BaseSecurity] = None,
        protocol: Optional[str] = None,
        protocol_version: Optional[str] = "custom",
        **kwargs: Any,
    ) -> None:
        """Redis broker.

        Args:
            url : URL of the Redis server
            polling_interval : interval in seconds to poll the Redis server for new messages (default: None)
            protocol : protocol of the Redis server (default: None)
            protocol_version : protocol version of the Redis server (default: "custom")
            security : security settings for the Redis server (default: None)
            kwargs : additional keyword arguments
        """
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
        """Connect to the Redis server.

        Args:
            args : additional positional arguments
            kwargs : additional keyword arguments
        """
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
        exc_tb: Optional[TracebackType] = None,
    ) -> None:
        if self._connection is not None:
            await self._connection.aclose()  # type: ignore[attr-defined]

        await super()._close(exc_type, exc_val, exc_tb)

    async def start(self) -> None:
        await super().start()

        assert self._producer and self._connection, NOT_CONNECTED_YET  # nosec B101

        for handler in self.handlers.values():
            self._log(
                f"`{handler.call_name}` waiting for messages",
                extra=handler.get_log_context(None),
            )
            await handler.start(
                self._connection,
                producer=self._producer,
            )

    @override
    def subscriber(  # type: ignore[override]
        self,
        channel: Union[Channel, PubSub, None] = None,
        *,
        list: Union[Channel, ListSub, None] = None,
        stream: Union[Channel, StreamSub, None] = None,
        # broker arguments
        dependencies: Sequence[Depends] = (),
        parser: Optional["CustomParser[AnyRedisDict]"] = None,
        decoder: Optional["CustomDecoder[RedisMessage]"] = None,
        middlewares: Iterable["SubscriberMiddleware"] = (),
        filter: Filter["RedisMessage"] = default_filter,
        retry: bool = False,
        no_ack: bool = False,
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        include_in_schema: bool = True,
        get_dependent: Optional[Any] = None,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[Any, P_HandlerParams, T_HandlerReturn],
    ]:
        channel = PubSub.validate(channel)
        list = ListSub.validate(list)
        stream = StreamSub.validate(stream)

        if (any_of := channel or list or stream) is None:
            raise ValueError(INCORRECT_SETUP_MSG)

        if all((channel, list)):
            raise ValueError("You can't use `PubSub` and `ListSub` both")
        elif all((channel, stream)):
            raise ValueError("You can't use `PubSub` and `StreamSub` both")
        elif all((list, stream)):
            raise ValueError("You can't use `ListSub` and `StreamSub` both")

        self._setup_log_context(channel=any_of.name)
        super().subscriber()

        key = Handler.get_routing_hash(any_of)
        handler = self.handlers[key] = self.handlers.get(key) or Handler.create(  # type: ignore[abstract]
            channel=channel,
            list=list,
            stream=stream,
            # base options
            extra_context={},
            graceful_timeout=self.graceful_timeout,
            middlewares=self.middlewares,
            watcher=get_watcher_context(self.logger, no_ack, retry),
            # AsyncAPI
            title_=title,
            description_=description,
            include_in_schema=include_in_schema,
        )

        return handler.add_call(
            filter=filter,
            parser=parser or self._global_parser,
            decoder=decoder or self._global_decoder,
            dependencies=(*self.dependencies, *dependencies),
            middlewares=middlewares,
            # wrapper kwargs
            is_validate=self._is_validate,
            apply_types=self._is_apply_types,
            get_dependent=get_dependent,
        )

    @override
    def publisher(  # type: ignore[override]
        self,
        channel: Union[Channel, PubSub, None] = None,
        list: Union[Channel, ListSub, None] = None,
        stream: Union[Channel, StreamSub, None] = None,
        headers: Optional[AnyDict] = None,
        reply_to: str = "",
        middlewares: Iterable[PublisherMiddleware] = (),
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
        publisher = self._publishers.get(key) or Publisher(
            channel=channel,
            list=list,
            stream=stream,
            headers=headers,
            reply_to=reply_to,
            middlewares=middlewares,
            # AsyncAPI
            title_=title,
            description_=description,
            schema_=schema,
            include_in_schema=include_in_schema,
        )
        super().publisher(key, publisher)
        if self._producer is not None:
            publisher._producer = self._producer
        return publisher

    @override
    async def publish(  # type: ignore[override]
        self,
        message: SendableMessage,
        *args: Any,
        **kwargs: Any,
    ) -> Optional[DecodedMessage]:
        async with AsyncExitStack() as stack:
            for m in self.middlewares:
                message = await stack.enter_async_context(
                    m().publish_scope(message, *args, **kwargs)
                )

            assert self._producer, NOT_CONNECTED_YET  # nosec B101
            return await self._producer.publish(message, *args, **kwargs)

    async def publish_batch(
        self,
        *messages: Any,
        **kwargs: Any,
    ) -> None:
        async with AsyncExitStack() as stack:
            wrapped_messages = [
                await stack.enter_async_context(
                    middleware().publish_scope(msg, **kwargs)
                )
                for msg in messages
                for middleware in self.middlewares
            ] or messages

            assert self._producer, NOT_CONNECTED_YET  # nosec B101
            return await self._producer.publish_batch(*wrapped_messages, **kwargs)
