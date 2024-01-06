import logging
from types import TracebackType
from typing import (
    Any,
    AsyncContextManager,
    Awaitable,
    Callable,
    Mapping,
    Sequence,
)

from fast_depends.dependencies import Depends
from redis.asyncio.client import Redis
from redis.asyncio.connection import BaseParser, Connection, DefaultParser, Encoder
from typing_extensions import TypeAlias, override

from faststream.asyncapi import schema as asyncapi
from faststream.broker.core.asynchronous import BrokerAsyncUsecase, default_filter
from faststream.broker.message import StreamMessage
from faststream.broker.middlewares import BaseMiddleware
from faststream.broker.types import (
    CustomDecoder,
    CustomParser,
    Filter,
    P_HandlerParams,
    T_HandlerReturn,
    WrappedReturn,
)
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.log import access_logger
from faststream.redis.asyncapi import Handler, Publisher
from faststream.redis.message import AnyRedisDict, RedisMessage
from faststream.redis.producer import RedisFastProducer
from faststream.redis.schemas import ListSub, PubSub, StreamSub
from faststream.redis.shared.logging import RedisLoggingMixin
from faststream.security import BaseSecurity
from faststream.types import AnyDict, DecodedMessage, SendableMessage

Channel: TypeAlias = str

class RedisBroker(
    RedisLoggingMixin,
    BrokerAsyncUsecase[AnyRedisDict, "Redis[bytes]"],
):
    url: str
    handlers: dict[int, Handler]
    _publishers: dict[int, Publisher]

    _producer: RedisFastProducer | None

    def __init__(
        self,
        url: str = "redis://localhost:6379",
        polling_interval: float | None = None,
        *,
        host: str = "localhost",
        port: str | int = 6379,
        db: str | int = 0,
        client_name: str | None = None,
        health_check_interval: float = 0,
        max_connections: int | None = None,
        socket_timeout: float | None = None,
        socket_connect_timeout: float | None = None,
        socket_read_size: int = 65536,
        socket_keepalive: bool = False,
        socket_keepalive_options: Mapping[int, int | bytes] | None = None,
        socket_type: int = 0,
        retry_on_timeout: bool = False,
        encoding: str = "utf-8",
        encoding_errors: str = "strict",
        decode_responses: bool = False,
        parser_class: type[BaseParser] = DefaultParser,
        connection_class: type[Connection] = Connection,
        encoder_class: type[Encoder] = Encoder,
        security: BaseSecurity | None = None,
        # broker args
        graceful_timeout: float | None = None,
        apply_types: bool = True,
        validate: bool = True,
        dependencies: Sequence[Depends] = (),
        parser: CustomParser[AnyRedisDict, RedisMessage] | None = None,
        decoder: CustomDecoder[RedisMessage] | None = None,
        middlewares: Sequence[Callable[[AnyRedisDict], BaseMiddleware]] | None = None,
        # AsyncAPI args
        asyncapi_url: str | None = None,
        protocol: str | None = None,
        protocol_version: str | None = "custom",
        description: str | None = None,
        tags: Sequence[asyncapi.Tag] | None = None,
        # logging args
        logger: logging.Logger | None = access_logger,
        log_level: int = logging.INFO,
        log_fmt: str | None = None,
    ) -> None: ...
    async def connect(
        self,
        url: str = "redis://localhost:6379",
        host: str = "localhost",
        port: str | int = 6379,
        db: str | int = 0,
        client_name: str | None = None,
        health_check_interval: float = 0,
        max_connections: int | None = None,
        socket_timeout: float | None = None,
        socket_connect_timeout: float | None = None,
        socket_read_size: int = 65536,
        socket_keepalive: bool = False,
        socket_keepalive_options: Mapping[int, int | bytes] | None = None,
        socket_type: int = 0,
        retry_on_timeout: bool = False,
        encoding: str = "utf-8",
        encoding_errors: str = "strict",
        decode_responses: bool = False,
        parser_class: type[BaseParser] = DefaultParser,
        connection_class: type[Connection] = Connection,
        encoder_class: type[Encoder] = Encoder,
        security: BaseSecurity | None = None,
    ) -> Redis[bytes]: ...
    @override
    async def _connect(  # type: ignore[override]
        self,
        url: str,
        host: str = "localhost",
        port: str | int = 6379,
        db: str | int = 0,
        client_name: str | None = None,
        health_check_interval: float = 0,
        max_connections: int | None = None,
        socket_timeout: float | None = None,
        socket_connect_timeout: float | None = None,
        socket_read_size: int = 65536,
        socket_keepalive: bool = False,
        socket_keepalive_options: Mapping[int, int | bytes] | None = None,
        socket_type: int = 0,
        retry_on_timeout: bool = False,
        encoding: str = "utf-8",
        encoding_errors: str = "strict",
        decode_responses: bool = False,
        parser_class: type[BaseParser] = DefaultParser,
        connection_class: type[Connection] = Connection,
        encoder_class: type[Encoder] = Encoder,
        security: BaseSecurity | None = None,
    ) -> Redis[bytes]: ...
    async def _close(
        self,
        exc_type: type[BaseException] | None = None,
        exc_val: BaseException | None = None,
        exec_tb: TracebackType | None = None,
    ) -> None: ...
    async def start(self) -> None: ...
    def _process_message(
        self,
        func: Callable[[StreamMessage[Any]], Awaitable[T_HandlerReturn]],
        watcher: Callable[..., AsyncContextManager[None]],
        **kwargs: Any,
    ) -> Callable[
        [StreamMessage[Any]],
        Awaitable[WrappedReturn[T_HandlerReturn]],
    ]: ...
    @override
    def subscriber(  # type: ignore[override]
        self,
        channel: Channel | PubSub | None = None,
        *,
        list: Channel | ListSub | None = None,
        stream: Channel | StreamSub | None = None,
        # broker arguments
        dependencies: Sequence[Depends] = (),
        parser: CustomParser[AnyRedisDict, RedisMessage] | None = None,
        decoder: CustomDecoder[RedisMessage] | None = None,
        middlewares: Sequence[Callable[[AnyRedisDict], BaseMiddleware]] | None = None,
        filter: Filter[RedisMessage] = default_filter,
        no_ack: bool = False,
        # AsyncAPI information
        title: str | None = None,
        description: str | None = None,
        include_in_schema: bool = True,
        **__service_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[Any, P_HandlerParams, T_HandlerReturn],
    ]: ...
    @override
    def publisher(  # type: ignore[override]
        self,
        channel: Channel | PubSub | None = None,
        list: Channel | ListSub | None = None,
        stream: Channel | StreamSub | None = None,
        headers: AnyDict | None = None,
        reply_to: str = "",
        # AsyncAPI information
        title: str | None = None,
        description: str | None = None,
        schema: Any | None = None,
        include_in_schema: bool = True,
    ) -> Publisher: ...
    @override
    async def publish(  # type: ignore[override]
        self,
        message: SendableMessage,
        channel: str | None = None,
        reply_to: str = "",
        headers: AnyDict | None = None,
        correlation_id: str | None = None,
        *,
        list: str | None = None,
        stream: str | None = None,
        rpc: bool = False,
        rpc_timeout: float | None = 30.0,
        raise_timeout: bool = False,
    ) -> DecodedMessage | None: ...
    async def publish_batch(
        self,
        *msgs: SendableMessage,
        list: str,
    ) -> None: ...
