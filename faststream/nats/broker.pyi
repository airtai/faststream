import logging
import ssl
from types import TracebackType
from typing import (
    Any,
    AsyncContextManager,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Type,
    Union,
)

from fast_depends.dependencies import Depends
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
    Client,
    Credentials,
    ErrorCallback,
    JWTCallback,
    SignatureCallback,
)
from nats.aio.msg import Msg
from nats.js import api
from nats.js.client import JetStreamContext

from faststream._compat import override
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
from faststream.nats.asyncapi import Handler, Publisher
from faststream.nats.js_stream import JStream
from faststream.nats.message import NatsMessage
from faststream.nats.producer import NatsFastProducer, NatsJSFastProducer
from faststream.nats.pull_sub import PullSub
from faststream.nats.shared.logging import NatsLoggingMixin
from faststream.types import DecodedMessage, SendableMessage

Subject = str

class NatsBroker(
    NatsLoggingMixin,
    BrokerAsyncUsecase[Msg, Client],
):
    stream: Optional[JetStreamContext]

    handlers: Dict[Subject, Handler]
    _publishers: Dict[Subject, Publisher]
    _producer: Optional[NatsFastProducer]
    _js_producer: Optional[NatsJSFastProducer]

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
        # broker args
        apply_types: bool = True,
        validate: bool = True,
        dependencies: Sequence[Depends] = (),
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
    ) -> Client: ...
    @override
    async def _connect(  # type: ignore[override]
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
    ) -> Client: ...
    async def _close(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exec_tb: Optional[TracebackType] = None,
    ) -> None: ...
    async def start(self) -> None: ...
    def _process_message(
        self,
        func: Callable[[StreamMessage[Msg]], Awaitable[T_HandlerReturn]],
        watcher: Callable[..., AsyncContextManager[None]],
        **kwargs: Any,
    ) -> Callable[[StreamMessage[Msg]], Awaitable[WrappedReturn[T_HandlerReturn]],]: ...
    def _log_connection_broken(
        self,
        error_cb: Optional[ErrorCallback] = None,
    ) -> ErrorCallback: ...
    def _log_reconnected(
        self,
        cb: Optional[Callback] = None,
    ) -> Callback: ...
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
    @override
    async def publish(  # type: ignore[override]
        self,
        message: SendableMessage,
        subject: str,
        headers: Optional[Dict[str, str]] = None,
        reply_to: str = "",
        correlation_id: Optional[str] = None,
        # JS arguments
        stream: Optional[str] = None,
        timeout: Optional[float] = None,
        *,
        rpc: bool = False,
        rpc_timeout: Optional[float] = 30.0,
        raise_timeout: bool = False,
    ) -> Optional[DecodedMessage]: ...
