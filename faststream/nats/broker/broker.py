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
from nats.errors import Error
from nats.js import api
from nats.js.client import (
    DEFAULT_JS_SUB_PENDING_BYTES_LIMIT,
    DEFAULT_JS_SUB_PENDING_MSGS_LIMIT,
)
from nats.js.errors import BadRequestError
from typing_extensions import Annotated, Doc, deprecated, override

from faststream.__about__ import SERVICE_NAME
from faststream.broker.core.broker import BrokerUsecase, default_filter
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
        CustomDecoder,
        CustomParser,
        Filter,
        PublisherMiddleware,
        SubscriberMiddleware,
    )
    from faststream.nats.message import NatsMessage
    from faststream.nats.schemas import JStream, PullSub
    from faststream.security import BaseSecurity
    from faststream.types import AnyDict, DecodedMessage, SendableMessage

    class NatsInitKwargs(TypedDict, total=False):
        """NatsBroker.connect() method type hints."""

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
        servers: Annotated[
            Union[str, Iterable[str]],
            Doc("NATS cluster addresses to connect."),
        ] = ("nats://localhost:4222",),
        *,
        error_cb: Annotated[
            Optional["ErrorCallback"],
            Doc("Callback to report errors."),
        ] = None,
        disconnected_cb: Annotated[
            Optional["Callback"],
            Doc("Callback to report disconnection from NATS."),
        ] = None,
        closed_cb: Annotated[
            Optional["Callback"],
            Doc("Callback to report when client stops reconnection to NATS."),
        ] = None,
        discovered_server_cb: Annotated[
            Optional["Callback"],
            Doc("Callback to report when a new server joins the cluster."),
        ] = None,
        reconnected_cb: Annotated[
            Optional["Callback"], Doc("Callback to report success reconnection.")
        ] = None,
        name: Annotated[
            Optional[str],
            Doc("Label the connection with name (shown in NATS monitoring)."),
        ] = SERVICE_NAME,
        pedantic: Annotated[
            bool,
            Doc(
                "Turn on NATS server pedantic mode that performs extra checks on the protocol. "
                "https://docs.nats.io/using-nats/developer/connecting/misc#turn-on-pedantic-mode"
            ),
        ] = False,
        verbose: Annotated[
            bool,
            Doc("Verbose mode produce more feedback about code execution."),
        ] = False,
        allow_reconnect: Annotated[
            bool,
            Doc("Whether recover connection automatically or not."),
        ] = True,
        connect_timeout: Annotated[
            int,
            Doc("Timeout in seconds to establish connection with NATS server."),
        ] = DEFAULT_CONNECT_TIMEOUT,
        reconnect_time_wait: Annotated[
            int,
            Doc("Time in seconds to wait for reestablish connection to NATS server"),
        ] = DEFAULT_RECONNECT_TIME_WAIT,
        max_reconnect_attempts: Annotated[
            int,
            Doc("Maximum attemps number to reconnect to NATS server."),
        ] = DEFAULT_MAX_RECONNECT_ATTEMPTS,
        ping_interval: Annotated[
            int,
            Doc("Interval in seconds to ping."),
        ] = DEFAULT_PING_INTERVAL,
        max_outstanding_pings: Annotated[
            int,
            Doc("Maximum number of failed pings"),
        ] = DEFAULT_MAX_OUTSTANDING_PINGS,
        dont_randomize: Annotated[
            bool,
            Doc(
                "Boolean indicating should client randomly shuffle servers list for reconnection randomness."
            ),
        ] = False,
        flusher_queue_size: Annotated[
            int, Doc("Max count of commands awaiting to be flushed to the socket")
        ] = DEFAULT_MAX_FLUSHER_QUEUE_SIZE,
        no_echo: Annotated[
            bool,
            Doc("Boolean indicating should commands be echoed."),
        ] = False,
        tls: Annotated[
            Optional["ssl.SSLContext"],
            Doc("Some SSL context to make NATS connections secure."),
        ] = None,
        tls_hostname: Annotated[
            Optional[str],
            Doc("Hostname for TLS."),
        ] = None,
        user: Annotated[
            Optional[str],
            Doc("Username for NATS auth."),
        ] = None,
        password: Annotated[
            Optional[str],
            Doc("Username password for NATS auth."),
        ] = None,
        token: Annotated[
            Optional[str],
            Doc("Auth token for NATS auth."),
        ] = None,
        drain_timeout: Annotated[
            int,
            Doc("Timeout in seconds to drain subscriptions."),
        ] = DEFAULT_DRAIN_TIMEOUT,
        signature_cb: Annotated[
            Optional["SignatureCallback"],
            Doc(
                "A callback used to sign a nonce from the server while "
                "authenticating with nkeys. The user should sign the nonce and "
                "return the base64 encoded signature."
            ),
        ] = None,
        user_jwt_cb: Annotated[
            Optional["JWTCallback"],
            Doc(
                "A callback used to fetch and return the account "
                "signed JWT for this user."
            ),
        ] = None,
        user_credentials: Annotated[
            Optional["Credentials"],
            Doc("A user credentials file or tuple of files."),
        ] = None,
        nkeys_seed: Annotated[
            Optional[str],
            Doc("Nkeys seed to be used."),
        ] = None,
        inbox_prefix: Annotated[
            Union[str, bytes],
            Doc(
                "Prefix for generating unique inboxes, subjects with that prefix and NUID.ß"
            ),
        ] = DEFAULT_INBOX_PREFIX,
        pending_size: Annotated[
            int,
            Doc("Max size of the pending buffer for publishing commands."),
        ] = DEFAULT_PENDING_SIZE,
        flush_timeout: Annotated[
            Optional[float],
            Doc("Max duration to wait for a forced flush to occur."),
        ] = None,
        # broker args
        graceful_timeout: Annotated[
            Optional[float],
            Doc(
                "Graceful shutdown timeout. Broker waits for all running subscribers completion before shut down."
            ),
        ] = None,
        apply_types: Annotated[
            bool,
            Doc("Whether to use FastDepends or not."),
        ] = True,
        validate: Annotated[
            bool,
            Doc("Whether to cast types using Pydantic validation."),
        ] = True,
        decoder: Annotated[
            Optional["CustomDecoder[StreamMessage[Msg]]"],
            Doc("Custom decoder object."),
        ] = None,
        parser: Annotated[
            Optional["CustomParser[Msg]"],
            Doc("Custom parser object."),
        ] = None,
        dependencies: Annotated[
            Iterable["Depends"],
            Doc("Dependencies to apply to all broker subscribers."),
        ] = (),
        middlewares: Annotated[
            Iterable["BrokerMiddleware[Msg]"],
            Doc("Middlewares to apply to all broker publishers/subscribers."),
        ] = (),
        # AsyncAPI args
        security: Annotated[
            Optional["BaseSecurity"],
            Doc(
                "Security options to connect broker and generate AsyncAPI server security information."
            ),
        ] = None,
        asyncapi_url: Annotated[
            Union[str, Iterable[str], None],
            Doc("AsyncAPI hardcoded server addresses. Use `servers` if not specified."),
        ] = None,
        protocol: Annotated[
            Optional[str],
            Doc("AsyncAPI server protocol."),
        ] = "nats",
        protocol_version: Annotated[
            Optional[str],
            Doc("AsyncAPI server protocol version."),
        ] = "custom",
        description: Annotated[
            Optional[str],
            Doc("AsyncAPI server description."),
        ] = None,
        tags: Annotated[
            Optional[Iterable[Union["asyncapi.Tag", "asyncapi.TagDict"]]],
            Doc("AsyncAPI server tags."),
        ] = None,
        # logging args
        logger: Annotated[
            Union[logging.Logger, None, object],
            Doc("User specified logger to pass into Context and log service messages."),
        ] = Parameter.empty,
        log_level: Annotated[
            int,
            Doc("Service messages log level."),
        ] = logging.INFO,
        log_fmt: Annotated[
            Optional[str],
            Doc("Default logger log format."),
        ] = None,
    ) -> None:
        """Initialize the NatsBroker object."""
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

    @override
    async def connect(  # type: ignore[override]
        self,
        servers: Annotated[
            Union[str, Iterable[str], object],
            Doc("NATS cluster addresses to connect."),
        ] = Parameter.empty,
        **kwargs: "Unpack[NatsInitKwargs]",
    ) -> "Client":
        """Connect broker object to NATS cluster.

        To startup subscribers too you should use `broker.start()` after/instead this method.
        """
        if servers is not Parameter.empty:
            kwargs["servers"] = servers

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
        """Connect broker to NATS cluster and startup all subscribers."""
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
        subject: Annotated[
            str,
            Doc("NATS subject to subscribe."),
        ],
        queue: Annotated[
            str,
            Doc(
                "Subscribers' NATS queue name. Subscribers with same queue name will be load balanced by the NATS "
                "server."
            ),
        ] = "",
        pending_msgs_limit: Annotated[
            Optional[int],
            Doc(
                "Limit of messages, considered by NATS server as possible to be delivered to the client without "
                "been answered. In case of NATS Core, if that limits exceeds, you will receive NATS 'Slow Consumer' "
                "error. "
                "That's literally means that your worker can't handle the whole load. In case of NATS JetStream, "
                "you will no longer receive messages until some of delivered messages will be acked in any way."
            ),
        ] = None,
        pending_bytes_limit: Annotated[
            Optional[int],
            Doc(
                "The number of bytes, considered by NATS server as possible to be delivered to the client without "
                "been answered. In case of NATS Core, if that limit exceeds, you will receive NATS 'Slow Consumer' "
                "error."
                "That's literally means that your worker can't handle the whole load. In case of NATS JetStream, "
                "you will no longer receive messages until some of delivered messages will be acked in any way."
            ),
        ] = None,
        # Core arguments
        max_msgs: Annotated[
            int,
            Doc("Consuming messages limiter. Automatically disconnect if reached."),
        ] = 0,
        # JS arguments
        durable: Annotated[
            Optional[str],
            Doc(
                "Name of the durable consumer to which the the subscription should be bound."
            ),
        ] = None,
        config: Annotated[
            Optional["api.ConsumerConfig"],
            Doc("Configuration of JetStream consumer to be subscribed with."),
        ] = None,
        ordered_consumer: Annotated[
            bool,
            Doc("Enable ordered consumer mode."),
        ] = False,
        idle_heartbeat: Annotated[
            Optional[float],
            Doc("Enable Heartbeats for a consumer to detect failures."),
        ] = None,
        flow_control: Annotated[
            bool,
            Doc("Enable Flow Control for a consumer."),
        ] = False,
        deliver_policy: Annotated[
            Optional["api.DeliverPolicy"],
            Doc("Deliver Policy to be used for subscription."),
        ] = None,
        headers_only: Annotated[
            Optional[bool],
            Doc(
                "Should be message delivered without payload, only headers and metadata."
            ),
        ] = None,
        # pull arguments
        pull_sub: Annotated[
            Optional["PullSub"],
            Doc(
                "NATS Pull consumer parameters container. "
                "Should be used with `stream` only."
            ),
        ] = None,
        inbox_prefix: Annotated[
            bytes,
            Doc(
                "Prefix for generating unique inboxes, subjects with that prefix and NUID."
            ),
        ] = api.INBOX_PREFIX,
        # custom
        ack_first: Annotated[
            bool,
            Doc("Whether to `ack` message at start of consuming or not."),
        ] = False,
        stream: Annotated[
            Union[str, "JStream", None],
            Doc("Subscribe to NATS Stream with `subject` filter."),
        ] = None,
        # broker arguments
        dependencies: Annotated[
            Iterable["Depends"],
            Doc("Dependencies list (`[Depends(),]`) to apply to the subscriber."),
        ] = (),
        parser: Annotated[
            Optional["CustomParser[Msg]"],
            Doc("Parser to map original **nats-py** Msg to FastStream one."),
        ] = None,
        decoder: Annotated[
            Optional["CustomDecoder[StreamMessage[Msg]]"],
            Doc("Function to decode FastStream msg bytes body to python objects."),
        ] = None,
        middlewares: Annotated[
            Iterable["SubscriberMiddleware"],
            Doc("Subscriber middlewares to wrap incoming message processing."),
        ] = (),
        filter: Annotated[
            "Filter[NatsMessage]",
            Doc(
                "Overload subscriber to consume various messages from the same source."
            ),
            deprecated(
                "Deprecated in **FastStream 0.5.0**. "
                "Please, create `subscriber` object and use it explicitly instead. "
                "Argument will be removed in **FastStream 0.6.0**."
            ),
        ] = default_filter,
        max_workers: Annotated[
            int,
            Doc("Number of workers to process messages concurrently."),
        ] = 1,
        retry: Annotated[
            bool,
            Doc("Whether to `nack` message at processing exception."),
        ] = False,
        no_ack: Annotated[
            bool,
            Doc("Whether to disable **FastStream** autoacknowledgement logic or not."),
        ] = False,
        # AsyncAPI information
        title: Annotated[
            Optional[str],
            Doc("AsyncAPI subscriber object title."),
        ] = None,
        description: Annotated[
            Optional[str],
            Doc(
                "AsyncAPI subscriber object description. "
                "Uses decorated docstring as default."
            ),
        ] = None,
        include_in_schema: Annotated[
            bool,
            Doc("Whetever to include operation in AsyncAPI schema or not."),
        ] = True,
        # Extra kwargs
        get_dependent: Annotated[
            Optional[Any],
            Doc("Service option to pass FastAPI-compatible callback."),
        ] = None,
    ) -> "WrapperProtocol[Msg]":
        """Creates NATS subscriber object.

        You can use it as a handler decorator `@broker.subscriber(...)`.
        """
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
            stream.add_subject(handler.subject)

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
        subject: Annotated[
            str,
            Doc("NATS subject to send message."),
        ],
        headers: Annotated[
            Optional[Dict[str, str]],
            Doc(
                "Message headers to store metainformation. "
                "**content-type** and **correlation_id** will be setted automatically by framework anyway. "
                "Can be overrided by `publish.headers` if specified."
            ),
        ] = None,
        reply_to: Annotated[
            str,
            Doc("NATS subject name to send response."),
        ] = "",
        # JS
        stream: Annotated[
            Union[str, "JStream", None],
            Doc(
                "This option validates that the target `subject` is in presented stream. "
                "Can be ommited without any effect."
            ),
        ] = None,
        timeout: Annotated[
            Optional[float],
            Doc("Timeout to send message to NATS."),
        ] = None,
        # specific
        middlewares: Annotated[
            Iterable["PublisherMiddleware"],
            Doc("Publisher middlewares to wrap outgoing messages."),
        ] = (),
        # AsyncAPI information
        title: Annotated[
            Optional[str],
            Doc("AsyncAPI publisher object title."),
        ] = None,
        description: Annotated[
            Optional[str],
            Doc("AsyncAPI publisher object description."),
        ] = None,
        schema: Annotated[
            Optional[Any],
            Doc(
                "AsyncAPI publishing message type. "
                "Should be any python-native object annotation or `pydantic.BaseModel`."
            ),
        ] = None,
        include_in_schema: Annotated[
            bool,
            Doc("Whetever to include operation in AsyncAPI schema or not."),
        ] = True,
    ) -> "Publisher":
        """Creates long-living and AsyncAPI-documented publisher object.

        You can use it as a handler decorator (handler should be decorated by `@broker.subscriber(...)` too) - `@broker.publisher(...)`.
        In such case publisher will publish your handler return value.

        Or you can create a publisher object to call it lately - `broker.publisher(...).publish(...)`.
        """
        if (stream := stream_builder.stream(stream)) is not None:
            stream.add_subject(subject)

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
        message: Annotated[
            "SendableMessage",
            Doc(
                "Message body to send. "
                "Can be any encodable object (native python types or `pydantic.BaseModel`)."
            ),
        ],
        subject: Annotated[
            str,
            Doc("NATS subject to send message."),
        ],
        headers: Annotated[
            Optional[Dict[str, str]],
            Doc(
                "Message headers to store metainformation. "
                "**content-type** and **correlation_id** will be setted automatically by framework anyway."
            ),
        ] = None,
        reply_to: Annotated[
            str,
            Doc("NATS subject name to send response."),
        ] = "",
        correlation_id: Annotated[
            Optional[str],
            Doc(
                "Manual message **correlation_id** setter. "
                "**correlation_id** is a useful option to trace messages."
            ),
        ] = None,
        stream: Annotated[
            Optional[str],
            Doc(
                "This option validates that the target subject is in presented stream. "
                "Can be ommited without any effect."
            ),
        ] = None,
        timeout: Annotated[
            Optional[float],
            Doc("Timeout to send message to NATS."),
        ] = None,
        *,
        rpc: Annotated[
            bool,
            Doc("Whether to wait for reply in blocking mode."),
        ] = False,
        rpc_timeout: Annotated[
            Optional[float],
            Doc("RPC reply waiting time."),
        ] = 30.0,
        raise_timeout: Annotated[
            bool,
            Doc(
                "Whetever to raise `TimeoutError` or return `None` at **rpc_timeout**. "
                "RPC request returns `None` at timeout by default."
            ),
        ] = False,
    ) -> Optional["DecodedMessage"]:
        """Publish message directly.

        This method allows you to publish message in not AsyncAPI-documented way. You can use it in another frameworks
        applications or to publish messages from time to time.

        Please, use `@broker.publisher(...)` or `broker.publisher(...).publish(...)` instead in a regular way.
        """
        kwargs = {
            "subject": subject,
            "headers": headers,
            "reply_to": reply_to,
            "correlation_id": correlation_id,
            "rpc": rpc,
            "rpc_timeout": rpc_timeout,
            "raise_timeout": raise_timeout,
        }

        if stream is None:
            assert self._producer, NOT_CONNECTED_YET  # nosec B101
            publisher = self._producer
        else:
            assert self._js_producer, NOT_CONNECTED_YET  # nosec B101
            publisher = self._js_producer
            kwargs.update(
                {
                    "stream": stream,
                    "timeout": timeout,
                }
            )

        async with AsyncExitStack() as stack:
            for m in self.middlewares:
                message = await stack.enter_async_context(
                    m().publish_scope(message, **kwargs)
                )

            return await publisher.publish(message, **kwargs)

    def __set_publisher_producer(
        self,
        publisher: "Publisher",
    ) -> None:
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

            if isinstance(err, Error) and self.__is_connected:
                self._log(
                    f"Connection broken with {err!r}", logging.WARNING, c, exc_info=err
                )
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

            if not self.__is_connected:
                self._log("Connection established", logging.INFO, c)
                self.__is_connected = True

        return wrapper
