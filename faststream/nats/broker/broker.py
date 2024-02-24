import logging
import warnings
from contextlib import AsyncExitStack
from inspect import Parameter
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Type,
    Union,
)

import nats
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
)
from nats.aio.subscription import (
    DEFAULT_SUB_PENDING_BYTES_LIMIT,
    DEFAULT_SUB_PENDING_MSGS_LIMIT,
)
from nats.js import api
from nats.js.client import (
    DEFAULT_JS_SUB_PENDING_BYTES_LIMIT,
    DEFAULT_JS_SUB_PENDING_MSGS_LIMIT,
)
from nats.js.errors import BadRequestError
from typing_extensions import override

from faststream.__about__ import __version__
from faststream.broker.core.broker import BrokerUsecase, default_filter
from faststream.broker.types import (
    CustomDecoder,
    CustomParser,
)
from faststream.broker.utils import get_watcher_context
from faststream.exceptions import NOT_CONNECTED_YET
from faststream.nats.asyncapi import AsyncAPIHandler, Publisher
from faststream.nats.broker.logging import NatsLoggingMixin
from faststream.nats.handler import BaseNatsHandler
from faststream.nats.helpers import stream_builder
from faststream.nats.producer import NatsFastProducer, NatsJSFastProducer
from faststream.nats.security import parse_security

if TYPE_CHECKING:
    import ssl
    from types import TracebackType

    from fast_depends.dependencies import Depends
    from nats.aio.client import (
        Callback,
        Client,
        Credentials,
        ErrorCallback,
        JWTCallback,
        SignatureCallback,
    )
    from nats.aio.msg import Msg
    from nats.js.client import JetStreamContext
    from typing_extensions import TypeAlias, TypedDict, Unpack

    from faststream.asyncapi import schema as asyncapi
    from faststream.broker.core.handler_wrapper_mixin import WrapperProtocol
    from faststream.broker.message import StreamMessage
    from faststream.broker.types import (
        BrokerMiddleware,
        Filter,
        PublisherMiddleware,
        SubscriberMiddleware,
    )
    from faststream.nats.message import NatsMessage
    from faststream.nats.schemas import JStream, PullSub
    from faststream.security import BaseSecurity
    from faststream.types import AnyDict, DecodedMessage, SendableMessage

    class NatsInitKwargs(TypedDict, total=False):
        servers: Union[str, Iterable[str]]
        error_cb: Optional["ErrorCallback"]
        disconnected_cb: Optional["Callback"]
        closed_cb: Optional["Callback"]
        discovered_server_cb: Optional["Callback"]
        reconnected_cb: Optional["Callback"]
        name: Optional[str]
        pedantic: bool
        verbose: bool
        allow_reconnect: bool
        connect_timeout: int
        reconnect_time_wait: int
        max_reconnect_attempts: int
        ping_interval: int
        max_outstanding_pings: int
        dont_randomize: bool
        flusher_queue_size: int
        no_echo: bool
        tls: Optional["ssl.SSLContext"]
        tls_hostname: Optional[str]
        user: Optional[str]
        password: Optional[str]
        token: Optional[str]
        drain_timeout: int
        signature_cb: Optional["SignatureCallback"]
        user_jwt_cb: Optional["JWTCallback"]
        user_credentials: Optional["Credentials"]
        nkeys_seed: Optional[str]
        inbox_prefix: Union[str, bytes]
        pending_size: int
        flush_timeout: Optional[float]

    Subject: TypeAlias = str


class NatsBroker(
    NatsLoggingMixin,
    BrokerUsecase["Msg", "Client"],
):
    """A class to represent a NATS broker."""

    url: List[str]
    stream: Optional["JetStreamContext"]

    handlers: Dict["Subject", "AsyncAPIHandler"]
    _publishers: Dict["Subject", "Publisher"]
    _producer: Optional["NatsFastProducer"]
    _js_producer: Optional["NatsJSFastProducer"]

    def __init__(
        self,
        servers: Union[str, Iterable[str]] = ("nats://localhost:4222",),
        *,
        error_cb: Optional["ErrorCallback"] = None,
        disconnected_cb: Optional["Callback"] = None,
        closed_cb: Optional["Callback"] = None,
        discovered_server_cb: Optional["Callback"] = None,
        reconnected_cb: Optional["Callback"] = None,
        name: Optional[str] = f"faststream-{__version__}",
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
        tls: Optional["ssl.SSLContext"] = None,
        tls_hostname: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
        drain_timeout: int = DEFAULT_DRAIN_TIMEOUT,
        signature_cb: Optional["SignatureCallback"] = None,
        user_jwt_cb: Optional["JWTCallback"] = None,
        user_credentials: Optional["Credentials"] = None,
        nkeys_seed: Optional[str] = None,
        inbox_prefix: Union[str, bytes] = DEFAULT_INBOX_PREFIX,
        pending_size: int = DEFAULT_PENDING_SIZE,
        flush_timeout: Optional[float] = None,
        # broker args
        graceful_timeout: Optional[float] = None,
        apply_types: bool = True,
        validate: bool = True,
        dependencies: Iterable["Depends"] = (),
        decoder: Optional[CustomDecoder["StreamMessage[Msg]"]] = None,
        parser: Optional[CustomParser["Msg"]] = None,
        middlewares: Iterable["BrokerMiddleware[Msg]"] = (),
        # AsyncAPI args
        security: Optional["BaseSecurity"] = None,
        asyncapi_url: Union[str, Iterable[str], None] = None,
        protocol: str = "nats",
        protocol_version: Optional[str] = "custom",
        description: Optional[str] = None,
        tags: Optional[Iterable["asyncapi.Tag"]] = None,
        # logging args
        logger: Union[logging.Logger, None, object] = Parameter.empty,
        log_level: int = logging.INFO,
        log_fmt: Optional[str] = None,
    ) -> None:
        """Initialize the NatsBroker object.

        Args:
            servers (Union[str, Sequence[str]]): The NATS server(s) to connect to.
            security (Optional[BaseSecurity]): The security options.
            protocol (str): The protocol to use.
            protocol_version (Optional[str]): The protocol version to use.
            **kwargs (Any): Additional keyword arguments.
        """
        if tls:  # pragma: no cover
            warnings.warn(
                (
                    "\nNATS `tls` option was deprecated and will be removed in 0.6.0"
                    "\nPlease, use `security` with `BaseSecurity` or `SASLPlaintext` instead"
                ),
                DeprecationWarning,
                stacklevel=2,
            )

        if user or password:
            warnings.warn(
                (
                    "\nNATS `user` and `password` options were deprecated and will be removed in 0.6.0"
                    "\nPlease, use `security` with `SASLPlaintext` instead"
                ),
                DeprecationWarning,
                stacklevel=2,
            )

        secure_kwargs = {
            "tls": tls,
            "user": user,
            "password": password,
        } | parse_security(security)

        servers = [servers] if isinstance(servers, str) else list(servers)

        if asyncapi_url is not None:
            if isinstance(asyncapi_url, str):
                asyncapi_url = [asyncapi_url]
            else:
                asyncapi_url = list(asyncapi_url)
        else:
            asyncapi_url = servers

        super().__init__(
            # NATS options
            servers=servers,
            name=name,
            verbose=verbose,
            allow_reconnect=allow_reconnect,
            reconnect_time_wait=reconnect_time_wait,
            max_reconnect_attempts=max_reconnect_attempts,
            no_echo=no_echo,
            pedantic=pedantic,
            inbox_prefix=inbox_prefix,
            pending_size=pending_size,
            connect_timeout=connect_timeout,
            drain_timeout=drain_timeout,
            flush_timeout=flush_timeout,
            ping_interval=ping_interval,
            max_outstanding_pings=max_outstanding_pings,
            dont_randomize=dont_randomize,
            flusher_queue_size=flusher_queue_size,
            ## security
            tls_hostname=tls_hostname,
            token=token,
            user_credentials=user_credentials,
            nkeys_seed=nkeys_seed,
            **secure_kwargs,
            ## callbacks
            error_cb=self._log_connection_broken(error_cb),
            reconnected_cb=self._log_reconnected(reconnected_cb),
            disconnected_cb=disconnected_cb,
            closed_cb=closed_cb,
            discovered_server_cb=discovered_server_cb,
            signature_cb=signature_cb,
            user_jwt_cb=user_jwt_cb,
            # Basic args
            ## broker base
            graceful_timeout=graceful_timeout,
            apply_types=apply_types,
            validate=validate,
            dependencies=dependencies,
            decoder=decoder,
            parser=parser,
            middlewares=middlewares,
            ## AsyncAPI
            description=description,
            asyncapi_url=asyncapi_url,
            protocol=protocol,
            protocol_version=protocol_version,
            security=security,
            tags=tags,
            ## logging
            logger=logger,
            log_level=log_level,
            log_fmt=log_fmt,
        )

        self.__is_connected = False
        self._producer = None

        # JS options
        self.stream = None
        self._js_producer = None

    async def connect(self, **kwargs: "Unpack[NatsInitKwargs]") -> "Client":
        connection = await super().connect(**kwargs)
        for p in self._publishers.values():
            self.__set_publisher_producer(p)
        return connection

    async def _connect(self, **kwargs: Any) -> "Client":
        self.__is_connected = True
        connection = await nats.connect(**kwargs)

        self._producer = NatsFastProducer(
            connection=connection,
            decoder=self._global_decoder,
            parser=self._global_parser,
        )

        stream = self.stream = connection.jetstream()

        self._js_producer = NatsJSFastProducer(
            connection=stream,
            decoder=self._global_decoder,
            parser=self._global_parser,
        )

        return connection

    async def _close(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exc_tb: Optional["TracebackType"] = None,
    ) -> None:
        self._producer = None
        self._js_producer = None
        self.stream = None

        if self._connection is not None:
            await self._connection.drain()

        await super()._close(exc_type, exc_val, exc_tb)
        self.__is_connected = False

    async def start(self) -> None:
        await super().start()

        assert self._connection  # nosec B101
        assert self.stream, "Broker should be started already"  # nosec B101
        assert self._producer, "Broker should be started already"  # nosec B101

        # TODO: filter by already running handlers after TestClient refactor
        for handler in self.handlers.values():
            stream = handler.stream

            log_context = handler.get_log_context(None)

            if (is_js := stream is not None) and stream.declare:
                try:  # pragma: no branch
                    await self.stream.add_stream(
                        config=stream.config,
                        subjects=stream.subjects,
                    )

                except BadRequestError as e:
                    old_config = (await self.stream.stream_info(stream.name)).config

                    if (
                        e.description
                        == "stream name already in use with a different configuration"
                    ):
                        self._log(str(e), logging.WARNING, log_context)
                        await self.stream.update_stream(
                            config=stream.config,
                            subjects=tuple(
                                set(old_config.subjects or ()).union(stream.subjects)
                            ),
                        )

                    else:  # pragma: no cover
                        self._log(str(e), logging.ERROR, log_context, exc_info=e)

                finally:
                    # prevent from double declaration
                    stream.declare = False

            self._log(f"`{handler.call_name}` waiting for messages", extra=log_context)
            await handler.start(
                self.stream if is_js else self._connection,
                producer=self._producer,
            )

    @override
    def subscriber(  # type: ignore[override]
        self,
        subject: str,
        queue: str = "",
        pending_msgs_limit: Optional[int] = None,
        pending_bytes_limit: Optional[int] = None,
        # Core arguments
        max_msgs: int = 0,
        # JS arguments
        durable: Optional[str] = None,
        config: Optional["api.ConsumerConfig"] = None,
        ordered_consumer: bool = False,
        idle_heartbeat: Optional[float] = None,
        flow_control: bool = False,
        deliver_policy: Optional["api.DeliverPolicy"] = None,
        headers_only: Optional[bool] = None,
        # pull arguments
        pull_sub: Optional["PullSub"] = None,
        inbox_prefix: bytes = api.INBOX_PREFIX,
        # custom
        ack_first: bool = False,
        stream: Union[str, "JStream", None] = None,
        # broker arguments
        dependencies: Iterable["Depends"] = (),
        parser: Optional["CustomParser[Msg]"] = None,
        decoder: Optional["CustomDecoder[NatsMessage]"] = None,
        middlewares: Iterable["SubscriberMiddleware"] = (),
        filter: "Filter[NatsMessage]" = default_filter,
        max_workers: int = 1,
        retry: bool = False,
        no_ack: bool = False,
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        include_in_schema: bool = True,
        # Extra kwargs
        get_dependent: Optional[Any] = None,
    ) -> "WrapperProtocol[Msg]":
        super().subscriber()

        stream = stream_builder.stream(stream)

        if pull_sub is not None and stream is None:
            raise ValueError("Pull subscriber can be used only with a stream")

        self._setup_log_context(
            queue=queue,
            subject=subject,
            stream=getattr(stream, "name", ""),
        )

        extra_options: "AnyDict" = {
            "pending_msgs_limit": pending_msgs_limit
            or (
                DEFAULT_JS_SUB_PENDING_MSGS_LIMIT
                if stream
                else DEFAULT_SUB_PENDING_MSGS_LIMIT
            ),
            "pending_bytes_limit": pending_bytes_limit
            or (
                DEFAULT_JS_SUB_PENDING_BYTES_LIMIT
                if stream
                else DEFAULT_SUB_PENDING_BYTES_LIMIT
            ),
        }

        if stream:
            # TODO: pull & queue warning
            # TODO: push & durable warning

            extra_options.update(
                {
                    "durable": durable,
                    "stream": stream.name,
                    "config": config,
                }
            )

            if pull_sub is not None:
                extra_options.update({"inbox_prefix": inbox_prefix})

            else:
                extra_options.update(
                    {
                        "ordered_consumer": ordered_consumer,
                        "idle_heartbeat": idle_heartbeat,
                        "flow_control": flow_control,
                        "deliver_policy": deliver_policy,
                        "headers_only": headers_only,
                        "manual_ack": not ack_first,
                    }
                )

        else:
            extra_options.update(
                {
                    "max_msgs": max_msgs,
                }
            )

        key = BaseNatsHandler.get_routing_hash(subject)
        handler = self.handlers[key] = self.handlers.get(key) or AsyncAPIHandler.create(
            subject=subject,
            queue=queue,
            stream=stream,
            pull_sub=pull_sub,
            extra_options=extra_options,
            max_workers=max_workers,
            extra_context={},
            # base options
            graceful_timeout=self.graceful_timeout,
            middlewares=self.middlewares,
            watcher=get_watcher_context(self.logger, no_ack, retry),
            # AsyncAPI
            title_=title,
            description_=description,
            include_in_schema=include_in_schema,
        )

        if stream:
            stream.subjects.append(handler.subject)

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
        subject: str,
        headers: Optional[Dict[str, str]] = None,
        # Core
        reply_to: str = "",
        # JS
        stream: Union[str, "JStream", None] = None,
        timeout: Optional[float] = None,
        # specific
        middlewares: Iterable["PublisherMiddleware"] = (),
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        schema: Optional[Any] = None,
        include_in_schema: bool = True,
    ) -> "Publisher":
        if (stream := stream_builder.stream(stream)) is not None:
            stream.subjects.append(subject)

        publisher = self._publishers.get(subject) or Publisher(
            subject=subject,
            headers=headers,
            # Core
            reply_to=reply_to,
            # JS
            timeout=timeout,
            stream=stream,
            # Specific
            middlewares=middlewares,
            # AsyncAPI
            title_=title,
            description_=description,
            schema_=schema,
            include_in_schema=include_in_schema,
        )
        super().publisher(subject, publisher)
        self.__set_publisher_producer(publisher)
        return publisher

    @override
    async def publish(  # type: ignore[override]
        self,
        message: "SendableMessage",
        *args: Any,
        stream: Optional[str] = None,
        **kwargs: Any,
    ) -> Optional["DecodedMessage"]:
        if stream is None:
            assert self._producer, NOT_CONNECTED_YET  # nosec B101
            publisher = self._producer
        else:
            assert self._js_producer, NOT_CONNECTED_YET  # nosec B101
            publisher = self._js_producer
            kwargs["stream"] = stream

        async with AsyncExitStack() as stack:
            for m in self.middlewares:
                message = await stack.enter_async_context(
                    m().publish_scope(message, *args, **kwargs)
                )

            return await publisher.publish(message, *args, **kwargs)

    def __set_publisher_producer(self, publisher: "Publisher") -> None:
        if publisher.stream is not None:
            if self._js_producer is not None:
                publisher._producer = self._js_producer
        elif self._producer is not None:
            publisher._producer = self._producer

    def _log_connection_broken(
        self,
        error_cb: Optional["ErrorCallback"] = None,
    ) -> "ErrorCallback":
        c = BaseNatsHandler.build_log_context(None, "")

        async def wrapper(err: Exception) -> None:
            if error_cb is not None:
                await error_cb(err)

            if self.__is_connected is True:
                self._log(str(err), logging.WARNING, c, exc_info=err)
                self.__is_connected = False

        return wrapper

    def _log_reconnected(
        self,
        cb: Optional["Callback"] = None,
    ) -> "Callback":
        c = BaseNatsHandler.build_log_context(None, "")

        async def wrapper() -> None:
            if cb is not None:
                await cb()

            if self.__is_connected is False:
                self._log("Connection established", logging.INFO, c)
                self.__is_connected = True

        return wrapper
