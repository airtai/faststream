import ssl
from enum import Enum
from typing import (
    Any,
    Awaitable,
    Callable,
    Mapping,
    Sequence,
    overload,
)

from fast_depends.dependencies import Depends
from fastapi import params
from fastapi.datastructures import Default
from fastapi.routing import APIRoute
from fastapi.utils import generate_unique_id
from nats.aio.client import (
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_DRAIN_TIMEOUT,
    DEFAULT_INBOX_PREFIX,
    DEFAULT_MAX_FLUSHER_QUEUE_SIZE,
    DEFAULT_MAX_OUTSTANDING_PINGS,
    DEFAULT_MAX_RECONNECT_ATTEMPTS,
    DEFAULT_PENDING_SIZE,
    DEFAULT_PING_INTERVAL,
    DEFAULT_RECONNECT_TIME_WAIT,
    Callback,
    Credentials,
    ErrorCallback,
    JWTCallback,
    SignatureCallback,
)
from nats.aio.msg import Msg
from nats.js import api
from starlette import routing
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp, AppType, Lifespan
from typing_extensions import override

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
from faststream.nats.asyncapi import Publisher
from faststream.nats.broker import NatsBroker
from faststream.nats.js_stream import JStream
from faststream.nats.message import NatsMessage
from faststream.nats.pull_sub import PullSub

class NatsRouter(StreamRouter[Msg]):
    broker_class = NatsBroker
    broker: NatsBroker

    @override
    @staticmethod
    def _setup_log_context(  # type: ignore[override]
        main_broker: NatsBroker,
        including_broker: NatsBroker,
    ) -> None: ...

    # nosemgrep: python.lang.security.audit.hardcoded-password-default-argument.hardcoded-password-default-argument
    def __init__(
        self,
        servers: str | Sequence[str] = ("nats://localhost:4222",),
        *,
        error_cb: ErrorCallback | None = None,
        disconnected_cb: Callback | None = None,
        closed_cb: Callback | None = None,
        discovered_server_cb: Callback | None = None,
        reconnected_cb: Callback | None = None,
        name: str | None = None,
        pedantic: bool = False,
        verbose: bool = False,
        allow_reconnect: bool = True,
        connect_timeout: int = DEFAULT_CONNECT_TIMEOUT,
        reconnect_time_wait: int = DEFAULT_RECONNECT_TIME_WAIT,
        max_reconnect_attempts: int = DEFAULT_MAX_RECONNECT_ATTEMPTS,
        ping_interval: int = DEFAULT_PING_INTERVAL,
        max_outstanding_pings: int = DEFAULT_MAX_OUTSTANDING_PINGS,
        dont_randomize: bool = False,
        flusher_queue_size: int = DEFAULT_MAX_FLUSHER_QUEUE_SIZE,
        no_echo: bool = False,
        tls: ssl.SSLContext | None = None,
        tls_hostname: str | None = None,
        user: str | None = None,
        password: str | None = None,
        token: str | None = None,
        drain_timeout: int = DEFAULT_DRAIN_TIMEOUT,
        signature_cb: SignatureCallback | None = None,
        user_jwt_cb: JWTCallback | None = None,
        user_credentials: Credentials | None = None,
        nkeys_seed: str | None = None,
        inbox_prefix: str | bytes = DEFAULT_INBOX_PREFIX,
        pending_size: int = DEFAULT_PENDING_SIZE,
        flush_timeout: float | None = None,
        # Broker kwargs
        graceful_timeout: float | None = None,
        decoder: CustomDecoder[NatsMessage] | None = None,
        parser: CustomParser[Msg, NatsMessage] | None = None,
        middlewares: Sequence[Callable[[Msg], BaseMiddleware]] | None = None,
        # AsyncAPI args
        asyncapi_url: str | list[str] | None = None,
        protocol: str = "nats",
        protocol_version: str | None = "0.9.1",
        description: str | None = None,
        asyncapi_tags: Sequence[asyncapi.Tag] | None = None,
        schema_url: str | None = "/asyncapi",
        setup_state: bool = True,
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
    def add_api_mq_route(  # type: ignore[override]
        self,
        subject: str,
        *,
        endpoint: Callable[..., T_HandlerReturn],
        queue: str = "",
        pending_msgs_limit: int | None = None,
        pending_bytes_limit: int | None = None,
        # Core arguments
        max_msgs: int = 0,
        ack_first: bool = False,
        # JS arguments
        stream: str | JStream | None = None,
        durable: str | None = None,
        config: api.ConsumerConfig | None = None,
        ordered_consumer: bool = False,
        idle_heartbeat: float | None = None,
        flow_control: bool = False,
        deliver_policy: api.DeliverPolicy | None = None,
        headers_only: bool | None = None,
        # broker arguments
        dependencies: Sequence[Depends] = (),
        parser: CustomParser[Msg, NatsMessage] | None = None,
        decoder: CustomDecoder[NatsMessage] | None = None,
        middlewares: Sequence[Callable[[Msg], BaseMiddleware]] | None = None,
        filter: Filter[NatsMessage] = default_filter,
        retry: bool = False,
        # AsyncAPI information
        title: str | None = None,
        description: str | None = None,
        **__service_kwargs: Any,
    ) -> Callable[[Msg, bool], Awaitable[T_HandlerReturn]]: ...
    @override
    def subscriber(  # type: ignore[override]
        self,
        subject: str,
        queue: str = "",
        pending_msgs_limit: int | None = None,
        pending_bytes_limit: int | None = None,
        # Core arguments
        max_msgs: int = 0,
        ack_first: bool = False,
        # JS arguments
        stream: str | JStream | None = None,
        durable: str | None = None,
        config: api.ConsumerConfig | None = None,
        ordered_consumer: bool = False,
        idle_heartbeat: float | None = None,
        flow_control: bool = False,
        deliver_policy: api.DeliverPolicy | None = None,
        headers_only: bool | None = None,
        # pull arguments
        pull_sub: PullSub | None = None,
        inbox_prefix: bytes = api.INBOX_PREFIX,
        # broker arguments
        dependencies: Sequence[Depends] = (),
        parser: CustomParser[Msg, NatsMessage] | None = None,
        decoder: CustomDecoder[NatsMessage] | None = None,
        middlewares: Sequence[Callable[[Msg], BaseMiddleware]] | None = None,
        filter: Filter[NatsMessage] = default_filter,
        retry: bool = False,
        no_ack: bool = False,
        # AsyncAPI information
        title: str | None = None,
        description: str | None = None,
        include_in_schema: bool = True,
        **__service_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[Msg, P_HandlerParams, T_HandlerReturn],
    ]: ...
    @override
    def publisher(  # type: ignore[override]
        self,
        subject: str,
        headers: dict[str, str] | None = None,
        # Core
        reply_to: str = "",
        # JS
        stream: str | JStream | None = None,
        timeout: float | None = None,
        # AsyncAPI information
        title: str | None = None,
        description: str | None = None,
        schema: Any | None = None,
        include_in_schema: bool = True,
    ) -> Publisher: ...
    @overload
    def after_startup(
        self,
        func: Callable[[AppType], Mapping[str, Any]],
    ) -> Callable[[AppType], Mapping[str, Any]]: ...
    @overload
    def after_startup(
        self,
        func: Callable[[AppType], Awaitable[Mapping[str, Any]]],
    ) -> Callable[[AppType], Awaitable[Mapping[str, Any]]]: ...
    @overload
    def after_startup(
        self,
        func: Callable[[AppType], None],
    ) -> Callable[[AppType], None]: ...
    @overload
    def after_startup(
        self,
        func: Callable[[AppType], Awaitable[None]],
    ) -> Callable[[AppType], Awaitable[None]]: ...
