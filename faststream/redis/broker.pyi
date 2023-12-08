import logging
from types import TracebackType
from typing import (
    Any,
    AsyncContextManager,
    Awaitable,
    Callable,
    Dict,
    Mapping,
    Optional,
    Sequence,
    Type,
    Union,
)

from fast_depends.dependencies import Depends
from redis.asyncio.client import Redis
from redis.asyncio.connection import BaseParser, Connection, DefaultParser, Encoder

from faststream._compat import TypeAlias, override
from faststream.asyncapi import schema as asyncapi
from faststream.broker.core.asyncronous import BrokerAsyncUsecase, default_filter
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
    handlers: Dict[int, Handler]
    _publishers: Dict[int, Publisher]

    _producer: Optional[RedisFastProducer]

    def __init__(
        self,
        url: str = "redis://localhost:6379",
        polling_interval: Optional[float] = None,
        *,
        host: str = "localhost",
        port: Union[str, int] = 6379,
        db: Union[str, int] = 0,
        client_name: Optional[str] = None,
        health_check_interval: float = 0,
        max_connections: Optional[int] = None,
        socket_timeout: Optional[float] = None,
        socket_connect_timeout: Optional[float] = None,
        socket_read_size: int = 65536,
        socket_keepalive: bool = False,
        socket_keepalive_options: Optional[Mapping[int, Union[int, bytes]]] = None,
        socket_type: int = 0,
        retry_on_timeout: bool = False,
        encoding: str = "utf-8",
        encoding_errors: str = "strict",
        decode_responses: bool = False,
        parser_class: Type[BaseParser] = DefaultParser,
        connection_class: Type[Connection] = Connection,
        encoder_class: Type[Encoder] = Encoder,
        security: Optional[BaseSecurity] = None,
        # broker args
        apply_types: bool = True,
        validate: bool = True,
        dependencies: Sequence[Depends] = (),
        parser: Optional[CustomParser[AnyRedisDict, RedisMessage]] = None,
        decoder: Optional[CustomDecoder[RedisMessage]] = None,
        middlewares: Optional[
            Sequence[Callable[[AnyRedisDict], BaseMiddleware]]
        ] = None,
        # AsyncAPI args
        asyncapi_url: Optional[str] = None,
        protocol: Optional[str] = None,
        protocol_version: Optional[str] = "custom",
        description: Optional[str] = None,
        tags: Optional[Sequence[asyncapi.Tag]] = None,
        # logging args
        logger: Optional[logging.Logger] = access_logger,
        log_level: int = logging.INFO,
        log_fmt: Optional[str] = None,
    ) -> None: ...
    async def connect(
        self,
        url: str = "redis://localhost:6379",
        host: str = "localhost",
        port: Union[str, int] = 6379,
        db: Union[str, int] = 0,
        client_name: Optional[str] = None,
        health_check_interval: float = 0,
        max_connections: Optional[int] = None,
        socket_timeout: Optional[float] = None,
        socket_connect_timeout: Optional[float] = None,
        socket_read_size: int = 65536,
        socket_keepalive: bool = False,
        socket_keepalive_options: Optional[Mapping[int, Union[int, bytes]]] = None,
        socket_type: int = 0,
        retry_on_timeout: bool = False,
        encoding: str = "utf-8",
        encoding_errors: str = "strict",
        decode_responses: bool = False,
        parser_class: Type[BaseParser] = DefaultParser,
        connection_class: Type[Connection] = Connection,
        encoder_class: Type[Encoder] = Encoder,
        security: Optional[BaseSecurity] = None,
    ) -> "Redis[bytes]": ...
    @override
    async def _connect(  # type: ignore[override]
        self,
        url: str,
        host: str = "localhost",
        port: Union[str, int] = 6379,
        db: Union[str, int] = 0,
        client_name: Optional[str] = None,
        health_check_interval: float = 0,
        max_connections: Optional[int] = None,
        socket_timeout: Optional[float] = None,
        socket_connect_timeout: Optional[float] = None,
        socket_read_size: int = 65536,
        socket_keepalive: bool = False,
        socket_keepalive_options: Optional[Mapping[int, Union[int, bytes]]] = None,
        socket_type: int = 0,
        retry_on_timeout: bool = False,
        encoding: str = "utf-8",
        encoding_errors: str = "strict",
        decode_responses: bool = False,
        parser_class: Type[BaseParser] = DefaultParser,
        connection_class: Type[Connection] = Connection,
        encoder_class: Type[Encoder] = Encoder,
        security: Optional[BaseSecurity] = None,
    ) -> "Redis[bytes]": ...
    async def _close(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exec_tb: Optional[TracebackType] = None,
    ) -> None: ...
    async def start(self) -> None: ...
    def _process_message(
        self,
        func: Callable[[StreamMessage[Any]], Awaitable[T_HandlerReturn]],
        watcher: Callable[..., AsyncContextManager[None]],
        **kwargs: Any,
    ) -> Callable[[StreamMessage[Any]], Awaitable[WrappedReturn[T_HandlerReturn]],]: ...
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
        no_ack: bool = False,
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        include_in_schema: bool = True,
        **__service_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[Any, P_HandlerParams, T_HandlerReturn],
    ]: ...
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
    ) -> Publisher: ...
    @override
    async def publish(  # type: ignore[override]
        self,
        message: SendableMessage,
        channel: Optional[str] = None,
        reply_to: str = "",
        headers: Optional[AnyDict] = None,
        correlation_id: Optional[str] = None,
        *,
        list: Optional[str] = None,
        stream: Optional[str] = None,
        rpc: bool = False,
        rpc_timeout: Optional[float] = 30.0,
        raise_timeout: bool = False,
    ) -> Optional[DecodedMessage]: ...
    async def publish_batch(
        self,
        *msgs: SendableMessage,
        list: str,
    ) -> None: ...
