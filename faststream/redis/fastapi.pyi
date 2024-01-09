import logging
from enum import Enum
from typing import (
    Any,
    Callable,
    Mapping,
    Sequence,
)

from fast_depends.dependencies import Depends
from fastapi import params
from fastapi.datastructures import Default
from fastapi.routing import APIRoute
from fastapi.utils import generate_unique_id
from redis.asyncio.connection import BaseParser, Connection, DefaultParser, Encoder
from starlette import routing
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp, Lifespan
from typing_extensions import TypeAlias, override

from faststream.asyncapi import schema as asyncapi
from faststream.broker.core.asynchronous import default_filter
from faststream.broker.fastapi.router import StreamRouter
from faststream.broker.middlewares import BaseMiddleware
from faststream.broker.types import (
    CustomDecoder,
    CustomParser,
    Filter,
    P_HandlerParams,
    T_HandlerReturn,
)
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.log import access_logger
from faststream.redis.asyncapi import Publisher
from faststream.redis.broker import RedisBroker
from faststream.redis.message import AnyRedisDict, RedisMessage
from faststream.redis.schemas import ListSub, PubSub, StreamSub
from faststream.security import BaseSecurity
from faststream.types import AnyDict

Channel: TypeAlias = str

class RedisRouter(StreamRouter[AnyRedisDict]):
    broker_class = RedisBroker

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
        parser: CustomParser[AnyRedisDict, RedisMessage] | None = None,
        decoder: CustomDecoder[RedisMessage] | None = None,
        middlewares: Sequence[Callable[[AnyRedisDict], BaseMiddleware]] | None = None,
        # AsyncAPI args
        asyncapi_url: str | None = None,
        protocol: str | None = None,
        protocol_version: str | None = "custom",
        description: str | None = None,
        asyncapi_tags: Sequence[asyncapi.Tag] | None = None,
        schema_url: str | None = "/asyncapi",
        setup_state: bool = True,
        # logging args
        logger: logging.Logger | None = access_logger,
        log_level: int = logging.INFO,
        log_fmt: str | None = None,
        # FastAPI kwargs
        prefix: str = "",
        tags: list[str | Enum] | None = None,
        dependencies: Sequence[params.Depends] | None = None,
        default_response_class: type[Response] = Default(JSONResponse),
        responses: dict[int | str, dict[str, Any]] | None = None,
        callbacks: list[routing.BaseRoute] | None = None,
        routes: list[routing.BaseRoute] | None = None,
        redirect_slashes: bool = True,
        default: ASGIApp | None = None,
        dependency_overrides_provider: Any | None = None,
        route_class: type[APIRoute] = APIRoute,
        on_startup: Sequence[Callable[[], Any]] | None = None,
        on_shutdown: Sequence[Callable[[], Any]] | None = None,
        deprecated: bool | None = None,
        include_in_schema: bool = True,
        lifespan: Lifespan[Any] | None = None,
        generate_unique_id_function: Callable[[APIRoute], str] = Default(
            generate_unique_id
        ),
    ) -> None: ...
    @override
    @staticmethod
    def _setup_log_context(  # type: ignore[override]
        main_broker: RedisBroker,
        including_broker: RedisBroker,
    ) -> None: ...
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
