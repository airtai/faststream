import logging
from inspect import Parameter
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Iterable,
    Optional,
    Type,
    Union,
    cast,
)
from urllib.parse import urlparse

from aio_pika import connect_robust
from typing_extensions import Annotated, Doc, override

from faststream.__about__ import SERVICE_NAME
from faststream.broker.message import gen_cor_id
from faststream.exceptions import NOT_CONNECTED_YET
from faststream.rabbit.broker.logging import RabbitLoggingBroker
from faststream.rabbit.broker.registrator import RabbitRegistrator
from faststream.rabbit.publisher.producer import AioPikaFastProducer
from faststream.rabbit.schemas import (
    RABBIT_REPLY,
    RabbitExchange,
    RabbitQueue,
)
from faststream.rabbit.security import parse_security
from faststream.rabbit.subscriber.asyncapi import AsyncAPISubscriber
from faststream.rabbit.utils import RabbitDeclarer, build_url

if TYPE_CHECKING:
    from ssl import SSLContext
    from types import TracebackType

    from aio_pika import (
        IncomingMessage,
        RobustChannel,
        RobustConnection,
        RobustExchange,
        RobustQueue,
    )
    from aio_pika.abc import DateType, HeadersType, SSLOptions, TimeoutType
    from fast_depends.dependencies import Depends
    from pamqp.common import FieldTable
    from yarl import URL

    from faststream.asyncapi import schema as asyncapi
    from faststream.broker.types import (
        BrokerMiddleware,
        CustomCallable,
    )
    from faststream.rabbit.types import AioPikaSendableMessage
    from faststream.security import BaseSecurity
    from faststream.types import AnyDict, Decorator, LoggerProto


class RabbitBroker(
    RabbitRegistrator,
    RabbitLoggingBroker,
):
    """A class to represent a RabbitMQ broker."""

    url: str
    _producer: Optional["AioPikaFastProducer"]

    declarer: Optional[RabbitDeclarer]
    _channel: Optional["RobustChannel"]

    def __init__(
        self,
        url: Annotated[
            Union[str, "URL", None],
            Doc("RabbitMQ destination location to connect."),
        ] = "amqp://guest:guest@localhost:5672/",  # pragma: allowlist secret
        *,
        # connection args
        host: Annotated[
            Optional[str],
            Doc("Destination host. This option overrides `url` option host."),
        ] = None,
        port: Annotated[
            Optional[int],
            Doc("Destination port. This option overrides `url` option port."),
        ] = None,
        virtualhost: Annotated[
            Optional[str],
            Doc("RabbitMQ virtual host to use in the current broker connection."),
        ] = None,
        ssl_options: Annotated[
            Optional["SSLOptions"],
            Doc("Extra ssl options to establish connection."),
        ] = None,
        client_properties: Annotated[
            Optional["FieldTable"],
            Doc("Add custom client capability."),
        ] = None,
        timeout: Annotated[
            "TimeoutType",
            Doc("Connection establishement timeout."),
        ] = None,
        # channel args
        channel_number: Annotated[
            Optional[int],
            Doc("Specify the channel number explicit."),
        ] = None,
        publisher_confirms: Annotated[
            bool,
            Doc(
                "if `True` the `publish` method will "
                "return `bool` type after publish is complete."
                "Otherwise it will returns `None`."
            ),
        ] = True,
        on_return_raises: Annotated[
            bool,
            Doc(
                "raise an :class:`aio_pika.exceptions.DeliveryError`"
                "when mandatory message will be returned"
            ),
        ] = False,
        # broker args
        max_consumers: Annotated[
            Optional[int],
            Doc(
                "RabbitMQ channel `qos` option. "
                "It limits max messages processing in the same time count."
            ),
        ] = None,
        app_id: Annotated[
            Optional[str],
            Doc("Application name to mark outgoing messages by."),
        ] = SERVICE_NAME,
        # broker base args
        graceful_timeout: Annotated[
            Optional[float],
            Doc(
                "Graceful shutdown timeout. Broker waits for all running subscribers completion before shut down."
            ),
        ] = None,
        decoder: Annotated[
            Optional["CustomCallable"],
            Doc("Custom decoder object."),
        ] = None,
        parser: Annotated[
            Optional["CustomCallable"],
            Doc("Custom parser object."),
        ] = None,
        dependencies: Annotated[
            Iterable["Depends"],
            Doc("Dependencies to apply to all broker subscribers."),
        ] = (),
        middlewares: Annotated[
            Iterable["BrokerMiddleware[IncomingMessage]"],
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
            Optional[str],
            Doc("AsyncAPI hardcoded server addresses. Use `servers` if not specified."),
        ] = None,
        protocol: Annotated[
            Optional[str],
            Doc("AsyncAPI server protocol."),
        ] = None,
        protocol_version: Annotated[
            Optional[str],
            Doc("AsyncAPI server protocol version."),
        ] = "0.9.1",
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
            Union["LoggerProto", None, object],
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
        # FastDepends args
        apply_types: Annotated[
            bool,
            Doc("Whether to use FastDepends or not."),
        ] = True,
        validate: Annotated[
            bool,
            Doc("Whether to cast types using Pydantic validation."),
        ] = True,
        _get_dependant: Annotated[
            Optional[Callable[..., Any]],
            Doc("Custom library dependant generator callback."),
        ] = None,
        _call_decorators: Annotated[
            Iterable["Decorator"],
            Doc("Any custom decorator to apply to wrapped functions."),
        ] = (),
    ) -> None:
        security_args = parse_security(security)

        amqp_url = build_url(
            url,
            host=host,
            port=port,
            virtualhost=virtualhost,
            ssl_options=ssl_options,
            client_properties=client_properties,
            login=security_args.get("login"),
            password=security_args.get("password"),
            ssl=security_args.get("ssl"),
        )

        if asyncapi_url is None:
            asyncapi_url = str(amqp_url)

        # respect ascynapi_url argument scheme
        builded_asyncapi_url = urlparse(asyncapi_url)
        self.virtual_host = builded_asyncapi_url.path
        if protocol is None:
            protocol = builded_asyncapi_url.scheme

        super().__init__(
            url=str(amqp_url),
            ssl_context=security_args.get("ssl_context"),
            timeout=timeout,
            # channel args
            channel_number=channel_number,
            publisher_confirms=publisher_confirms,
            on_return_raises=on_return_raises,
            # Basic args
            graceful_timeout=graceful_timeout,
            dependencies=dependencies,
            decoder=decoder,
            parser=parser,
            middlewares=middlewares,
            # AsyncAPI args
            description=description,
            asyncapi_url=asyncapi_url,
            protocol=protocol or builded_asyncapi_url.scheme,
            protocol_version=protocol_version,
            security=security,
            tags=tags,
            # Logging args
            logger=logger,
            log_level=log_level,
            log_fmt=log_fmt,
            # FastDepends args
            apply_types=apply_types,
            validate=validate,
            _get_dependant=_get_dependant,
            _call_decorators=_call_decorators,
        )

        self._max_consumers = max_consumers

        self.app_id = app_id

        self._channel = None
        self.declarer = None

    @property
    def _subscriber_setup_extra(self) -> "AnyDict":
        return {
            **super()._subscriber_setup_extra,
            "app_id": self.app_id,
            "virtual_host": self.virtual_host,
            "declarer": self.declarer,
        }

    @property
    def _publisher_setup_extra(self) -> "AnyDict":
        return {
            **super()._publisher_setup_extra,
            "app_id": self.app_id,
            "virtual_host": self.virtual_host,
        }

    @override
    async def connect(  # type: ignore[override]
        self,
        url: Annotated[
            Union[str, "URL", object], Doc("RabbitMQ destination location to connect.")
        ] = Parameter.empty,
        *,
        host: Annotated[
            Optional[str],
            Doc("Destination host. This option overrides `url` option host."),
        ] = None,
        port: Annotated[
            Optional[int],
            Doc("Destination port. This option overrides `url` option port."),
        ] = None,
        virtualhost: Annotated[
            Optional[str],
            Doc("RabbitMQ virtual host to use in the current broker connection."),
        ] = None,
        ssl_options: Annotated[
            Optional["SSLOptions"],
            Doc("Extra ssl options to establish connection."),
        ] = None,
        client_properties: Annotated[
            Optional["FieldTable"],
            Doc("Add custom client capability."),
        ] = None,
        security: Annotated[
            Optional["BaseSecurity"],
            Doc(
                "Security options to connect broker and generate AsyncAPI server security information."
            ),
        ] = None,
        timeout: Annotated[
            "TimeoutType",
            Doc("Connection establishement timeout."),
        ] = None,
        # channel args
        channel_number: Annotated[
            Union[int, None, object],
            Doc("Specify the channel number explicit."),
        ] = Parameter.empty,
        publisher_confirms: Annotated[
            Union[bool, object],
            Doc(
                "if `True` the `publish` method will "
                "return `bool` type after publish is complete."
                "Otherwise it will returns `None`."
            ),
        ] = Parameter.empty,
        on_return_raises: Annotated[
            Union[bool, object],
            Doc(
                "raise an :class:`aio_pika.exceptions.DeliveryError`"
                "when mandatory message will be returned"
            ),
        ] = Parameter.empty,
    ) -> "RobustConnection":
        """Connect broker object to RabbitMQ.

        To startup subscribers too you should use `broker.start()` after/instead this method.
        """
        kwargs: AnyDict = {}

        if channel_number is not Parameter.empty:
            kwargs["channel_number"] = channel_number

        if publisher_confirms is not Parameter.empty:
            kwargs["publisher_confirms"] = publisher_confirms

        if on_return_raises is not Parameter.empty:
            kwargs["on_return_raises"] = on_return_raises

        if timeout:
            kwargs["timeout"] = timeout

        url = None if url is Parameter.empty else cast(Union[str, "URL"], url)

        if url or any(
            (host, port, virtualhost, ssl_options, client_properties, security)
        ):
            security_args = parse_security(security)

            kwargs["url"] = build_url(
                url,
                host=host,
                port=port,
                virtualhost=virtualhost,
                ssl_options=ssl_options,
                client_properties=client_properties,
                login=security_args.get("login"),
                password=security_args.get("password"),
                ssl=security_args.get("ssl"),
            )

            if ssl_context := security_args.get("ssl_context"):
                kwargs["ssl_context"] = ssl_context

        connection = await super().connect(**kwargs)

        return connection

    @override
    async def _connect(  # type: ignore[override]
        self,
        url: str,
        *,
        timeout: "TimeoutType",
        ssl_context: Optional["SSLContext"],
        channel_number: Optional[int],
        publisher_confirms: bool,
        on_return_raises: bool,
    ) -> "RobustConnection":
        connection = cast(
            "RobustConnection",
            await connect_robust(
                url,
                timeout=timeout,
                ssl_context=ssl_context,
            ),
        )

        if self._channel is None:  # pragma: no branch
            max_consumers = self._max_consumers
            channel = self._channel = cast(
                "RobustChannel",
                await connection.channel(
                    channel_number=channel_number,
                    publisher_confirms=publisher_confirms,
                    on_return_raises=on_return_raises,
                ),
            )

            declarer = self.declarer = RabbitDeclarer(channel)
            await declarer.declare_queue(RABBIT_REPLY)

            self._producer = AioPikaFastProducer(
                channel=channel,
                declarer=declarer,
                decoder=self._decoder,
                parser=self._parser,
            )

            if max_consumers:
                c = AsyncAPISubscriber.build_log_context(
                    None, RabbitQueue(""), RabbitExchange("")
                )
                self._log(f"Set max consumers to {max_consumers}", extra=c)
                await channel.set_qos(prefetch_count=int(max_consumers))

        return connection

    async def _close(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exc_tb: Optional["TracebackType"] = None,
    ) -> None:
        if self._channel is not None:
            if not self._channel.is_closed:
                await self._channel.close()

            self._channel = None

        self.declarer = None
        self._producer = None

        if self._connection is not None:
            await self._connection.close()

        await super()._close(exc_type, exc_val, exc_tb)

    async def start(self) -> None:
        """Connect broker to RabbitMQ and startup all subscribers."""
        await super().start()

        assert self.declarer, NOT_CONNECTED_YET  # nosec B101

        for publisher in self._publishers.values():
            if publisher.exchange is not None:
                await self.declare_exchange(publisher.exchange)

        for subscriber in self._subscribers.values():
            self._log(
                f"`{subscriber.call_name}` waiting for messages",
                extra=subscriber.get_log_context(None),
            )
            await subscriber.start()

    @override
    async def publish(  # type: ignore[override]
        self,
        message: Annotated[
            "AioPikaSendableMessage",
            Doc("Message body to send."),
        ] = None,
        queue: Annotated[
            Union["RabbitQueue", str],
            Doc("Message routing key to publish with."),
        ] = "",
        exchange: Annotated[
            Union["RabbitExchange", str, None],
            Doc("Target exchange to publish message to."),
        ] = None,
        *,
        routing_key: Annotated[
            str,
            Doc(
                "Message routing key to publish with. "
                "Overrides `queue` option if presented."
            ),
        ] = "",
        mandatory: Annotated[
            bool,
            Doc(
                "Client waits for confirmation that the message is placed to some queue. "
                "RabbitMQ returns message to client if there is no suitable queue."
            ),
        ] = True,
        immediate: Annotated[
            bool,
            Doc(
                "Client expects that there is consumer ready to take the message to work. "
                "RabbitMQ returns message to client if there is no suitable consumer."
            ),
        ] = False,
        timeout: Annotated[
            "TimeoutType",
            Doc("Send confirmation time from RabbitMQ."),
        ] = None,
        persist: Annotated[
            bool,
            Doc("Restore the message on RabbitMQ reboot."),
        ] = False,
        reply_to: Annotated[
            Optional[str],
            Doc(
                "Reply message routing key to send with (always sending to default exchange)."
            ),
        ] = None,
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
        # message args
        correlation_id: Annotated[
            Optional[str],
            Doc(
                "Manual message **correlation_id** setter. "
                "**correlation_id** is a useful option to trace messages."
            ),
        ] = None,
        headers: Annotated[
            Optional["HeadersType"],
            Doc("Message headers to store metainformation."),
        ] = None,
        content_type: Annotated[
            Optional[str],
            Doc(
                "Message **content-type** header. "
                "Used by application, not core RabbitMQ. "
                "Will be set automatically if not specified."
            ),
        ] = None,
        content_encoding: Annotated[
            Optional[str],
            Doc("Message body content encoding, e.g. **gzip**."),
        ] = None,
        expiration: Annotated[
            Optional["DateType"],
            Doc("Message expiration (lifetime) in seconds (or datetime or timedelta)."),
        ] = None,
        message_id: Annotated[
            Optional[str],
            Doc("Arbitrary message id. Generated automatically if not presented."),
        ] = None,
        timestamp: Annotated[
            Optional["DateType"],
            Doc("Message publish timestamp. Generated automatically if not presented."),
        ] = None,
        message_type: Annotated[
            Optional[str],
            Doc("Application-specific message type, e.g. **orders.created**."),
        ] = None,
        user_id: Annotated[
            Optional[str],
            Doc("Publisher connection User ID, validated if set."),
        ] = None,
        priority: Annotated[
            Optional[int],
            Doc("The message priority (0 by default)."),
        ] = None,
    ) -> Optional[Any]:
        """Publish message directly.

        This method allows you to publish message in not AsyncAPI-documented way. You can use it in another frameworks
        applications or to publish messages from time to time.

        Please, use `@broker.publisher(...)` or `broker.publisher(...).publish(...)` instead in a regular way.
        """
        routing = routing_key or RabbitQueue.validate(queue).routing
        correlation_id = correlation_id or gen_cor_id()

        return await super().publish(
            message,
            producer=self._producer,
            routing_key=routing,
            app_id=self.app_id,
            exchange=exchange,
            mandatory=mandatory,
            immediate=immediate,
            persist=persist,
            reply_to=reply_to,
            headers=headers,
            correlation_id=correlation_id,
            content_type=content_type,
            content_encoding=content_encoding,
            expiration=expiration,
            message_id=message_id,
            timestamp=timestamp,
            message_type=message_type,
            user_id=user_id,
            timeout=timeout,
            priority=priority,
            rpc=rpc,
            rpc_timeout=rpc_timeout,
            raise_timeout=raise_timeout,
        )

    async def declare_queue(
        self,
        queue: Annotated[
            "RabbitQueue",
            Doc("Queue object to create."),
        ],
    ) -> "RobustQueue":
        """Declares queue object in **RabbitMQ**."""
        assert self.declarer, NOT_CONNECTED_YET  # nosec B101
        return await self.declarer.declare_queue(queue)

    async def declare_exchange(
        self,
        exchange: Annotated[
            "RabbitExchange",
            Doc("Exchange object to create."),
        ],
    ) -> "RobustExchange":
        """Declares exchange object in **RabbitMQ**."""
        assert self.declarer, NOT_CONNECTED_YET  # nosec B101
        return await self.declarer.declare_exchange(exchange)
