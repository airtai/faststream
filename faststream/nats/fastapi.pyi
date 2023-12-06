import ssl
from enum import Enum
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    Type,
    Union,
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
from starlette.types import AppType, ASGIApp, Lifespan

from faststream._compat import override
from faststream.asyncapi import schema as asyncapi
from faststream.broker.core.asyncronous import default_filter
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
        servers: Union[str, Sequence[str]] = ("nats://localhost:4222",),  # noqa: B006
        *,
        error_cb: Optional[ErrorCallback] = None,
        disconnected_cb: Optional[Callback] = None,
        closed_cb: Optional[Callback] = None,
        discovered_server_cb: Optional[Callback] = None,
        reconnected_cb: Optional[Callback] = None,
        name: Optional[str] = None,
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
        tls: Optional[ssl.SSLContext] = None,
        tls_hostname: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
        drain_timeout: int = DEFAULT_DRAIN_TIMEOUT,
        signature_cb: Optional[SignatureCallback] = None,
        user_jwt_cb: Optional[JWTCallback] = None,
        user_credentials: Optional[Credentials] = None,
        nkeys_seed: Optional[str] = None,
        inbox_prefix: Union[str, bytes] = DEFAULT_INBOX_PREFIX,
        pending_size: int = DEFAULT_PENDING_SIZE,
        flush_timeout: Optional[float] = None,
        # Broker kwargs
        decoder: Optional[CustomDecoder[NatsMessage]] = None,
        parser: Optional[CustomParser[Msg, NatsMessage]] = None,
        middlewares: Optional[
            Sequence[
                Callable[
                    [Msg],
                    BaseMiddleware,
                ]
            ]
        ] = None,
        # AsyncAPI args
        asyncapi_url: Union[str, List[str], None] = None,
        protocol: str = "nats",
        protocol_version: Optional[str] = "0.9.1",
        description: Optional[str] = None,
        asyncapi_tags: Optional[Sequence[asyncapi.Tag]] = None,
        schema_url: Optional[str] = "/asyncapi",
        setup_state: bool = True,
        # FastAPI kwargs
        prefix: str = "",
        tags: Optional[List[Union[str, Enum]]] = None,
        dependencies: Optional[Sequence[params.Depends]] = None,
        default_response_class: Type[Response] = Default(JSONResponse),
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        callbacks: Optional[List[routing.BaseRoute]] = None,
        routes: Optional[List[routing.BaseRoute]] = None,
        redirect_slashes: bool = True,
        default: Optional[ASGIApp] = None,
        dependency_overrides_provider: Optional[Any] = None,
        route_class: Type[APIRoute] = APIRoute,
        on_startup: Optional[Sequence[Callable[[], Any]]] = None,
        on_shutdown: Optional[Sequence[Callable[[], Any]]] = None,
        deprecated: Optional[bool] = None,
        include_in_schema: bool = True,
        lifespan: Optional[Lifespan[Any]] = None,
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
        pending_msgs_limit: Optional[int] = None,
        pending_bytes_limit: Optional[int] = None,
        # Core arguments
        max_msgs: int = 0,
        ack_first: bool = False,
        # JS arguments
        stream: Union[str, JStream, None] = None,
        durable: Optional[str] = None,
        config: Optional[api.ConsumerConfig] = None,
        ordered_consumer: bool = False,
        idle_heartbeat: Optional[float] = None,
        flow_control: bool = False,
        deliver_policy: Optional[api.DeliverPolicy] = None,
        headers_only: Optional[bool] = None,
        # broker arguments
        dependencies: Sequence[Depends] = (),
        parser: Optional[CustomParser[Msg, NatsMessage]] = None,
        decoder: Optional[CustomDecoder[NatsMessage]] = None,
        middlewares: Optional[Sequence[Callable[[Msg], BaseMiddleware]]] = None,
        filter: Filter[NatsMessage] = default_filter,
        retry: bool = False,
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        **__service_kwargs: Any,
    ) -> Callable[[Msg, bool], Awaitable[T_HandlerReturn]]: ...
    @override
    def subscriber(  # type: ignore[override]
        self,
        subject: str,
        queue: str = "",
        pending_msgs_limit: Optional[int] = None,
        pending_bytes_limit: Optional[int] = None,
        # Core arguments
        max_msgs: int = 0,
        ack_first: bool = False,
        # JS arguments
        stream: Union[str, JStream, None] = None,
        durable: Optional[str] = None,
        config: Optional[api.ConsumerConfig] = None,
        ordered_consumer: bool = False,
        idle_heartbeat: Optional[float] = None,
        flow_control: bool = False,
        deliver_policy: Optional[api.DeliverPolicy] = None,
        headers_only: Optional[bool] = None,
        # pull arguments
        pull_sub: Optional[PullSub] = None,
        inbox_prefix: bytes = api.INBOX_PREFIX,
        # broker arguments
        dependencies: Sequence[Depends] = (),
        parser: Optional[CustomParser[Msg, NatsMessage]] = None,
        decoder: Optional[CustomDecoder[NatsMessage]] = None,
        middlewares: Optional[Sequence[Callable[[Msg], BaseMiddleware]]] = None,
        filter: Filter[NatsMessage] = default_filter,
        retry: bool = False,
        no_ack: bool = False,
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
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
        headers: Optional[Dict[str, str]] = None,
        # Core
        reply_to: str = "",
        # JS
        stream: Union[str, JStream, None] = None,
        timeout: Optional[float] = None,
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        schema: Optional[Any] = None,
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
