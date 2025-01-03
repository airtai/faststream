import logging
from collections.abc import Iterable, Sequence
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Callable,
    Optional,
    Union,
    cast,
)
from urllib.parse import urlparse

import anyio
from aio_pika import IncomingMessage, RobustConnection, connect_robust
from typing_extensions import Doc, override

from faststream.__about__ import SERVICE_NAME
from faststream._internal.broker.broker import ABCBroker, BrokerUsecase
from faststream._internal.constants import EMPTY
from faststream._internal.publisher.proto import PublisherProto
from faststream.message import gen_cor_id
from faststream.rabbit.helpers.declarer import RabbitDeclarer
from faststream.rabbit.publisher.producer import AioPikaFastProducer
from faststream.rabbit.response import RabbitPublishCommand
from faststream.rabbit.schemas import (
    RABBIT_REPLY,
    RabbitExchange,
    RabbitQueue,
)
from faststream.rabbit.security import parse_security
from faststream.rabbit.utils import build_url
from faststream.response.publish_type import PublishType

from .logging import make_rabbit_logger_state
from .registrator import RabbitRegistrator

if TYPE_CHECKING:
    from ssl import SSLContext
    from types import TracebackType

    import aiormq
    from aio_pika import (
        RobustChannel,
        RobustExchange,
        RobustQueue,
    )
    from aio_pika.abc import DateType, HeadersType, SSLOptions, TimeoutType
    from fast_depends.dependencies import Dependant
    from fast_depends.library.serializer import SerializerProto
    from pamqp.common import FieldTable
    from yarl import URL

    from faststream._internal.basic_types import AnyDict, Decorator, LoggerProto
    from faststream._internal.types import (
        BrokerMiddleware,
        CustomCallable,
    )
    from faststream.rabbit.message import RabbitMessage
    from faststream.rabbit.types import AioPikaSendableMessage
    from faststream.security import BaseSecurity
    from faststream.specification.schema.extra import Tag, TagDict


class RabbitBroker(
    RabbitRegistrator,
    BrokerUsecase[IncomingMessage, RobustConnection],
):
    """A class to represent a RabbitMQ broker."""

    url: str

    _producer: "AioPikaFastProducer"
    declarer: RabbitDeclarer

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
            fail_fast: Annotated[
                bool,
                Doc(
                    "Broker startup raises `AMQPConnectionError` if RabbitMQ is unreachable.",
                ),
            ] = True,
            reconnect_interval: Annotated[
                "TimeoutType",
                Doc("Time to sleep between reconnection attempts."),
            ] = 5.0,
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
                    "Otherwise it will returns `None`.",
                ),
            ] = True,
            on_return_raises: Annotated[
                bool,
                Doc(
                    "raise an :class:`aio_pika.exceptions.DeliveryError`"
                    "when mandatory message will be returned",
                ),
            ] = False,
            # broker args
            max_consumers: Annotated[
                Optional[int],
                Doc(
                    "RabbitMQ channel `qos` option. "
                    "It limits max messages processing in the same time count.",
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
                    "Graceful shutdown timeout. Broker waits for all running subscribers completion before shut down.",
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
                Iterable["Dependant"],
                Doc("Dependencies to apply to all broker subscribers."),
            ] = (),
            middlewares: Annotated[
                Sequence["BrokerMiddleware[IncomingMessage]"],
                Doc("Middlewares to apply to all broker publishers/subscribers."),
            ] = (),
            routers: Annotated[
                Sequence["ABCBroker[IncomingMessage]"],
                Doc("Routers to apply to broker."),
            ] = (),
            # AsyncAPI args
            security: Annotated[
                Optional["BaseSecurity"],
                Doc(
                    "Security options to connect broker and generate AsyncAPI server security information.",
                ),
            ] = None,
            specification_url: Annotated[
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
                Iterable[Union["Tag", "TagDict"]],
                Doc("AsyncAPI server tags."),
            ] = (),
            # logging args
            logger: Annotated[
                Optional["LoggerProto"],
                Doc("User specified logger to pass into Context and log service messages."),
            ] = EMPTY,
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
            serializer: Optional["SerializerProto"] = EMPTY,
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

        if specification_url is None:
            specification_url = str(amqp_url)

        # respect ascynapi_url argument scheme
        built_asyncapi_url = urlparse(specification_url)
        self.virtual_host = built_asyncapi_url.path
        if protocol is None:
            protocol = built_asyncapi_url.scheme

        super().__init__(
            url=str(amqp_url),
            ssl_context=security_args.get("ssl_context"),
            timeout=timeout,
            fail_fast=fail_fast,
            reconnect_interval=reconnect_interval,
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
            routers=routers,
            # AsyncAPI args
            description=description,
            specification_url=specification_url,
            protocol=protocol or built_asyncapi_url.scheme,
            protocol_version=protocol_version,
            security=security,
            tags=tags,
            # Logging args
            logger_state=make_rabbit_logger_state(
                logger=logger,
                log_level=log_level,
                log_fmt=log_fmt,
            ),
            # FastDepends args
            apply_types=apply_types,
            serializer=serializer,
            _get_dependant=_get_dependant,
            _call_decorators=_call_decorators,
        )

        self._max_consumers = max_consumers

        self.app_id = app_id

        self._channel = None

        declarer = self.declarer = RabbitDeclarer()
        self._state.patch_value(
            producer=AioPikaFastProducer(
                declarer=declarer,
                decoder=self._decoder,
                parser=self._parser,
            )
        )

    @property
    def _subscriber_setup_extra(self) -> "AnyDict":
        return {
            **super()._subscriber_setup_extra,
            "app_id": self.app_id,
            "virtual_host": self.virtual_host,
            "declarer": self.declarer,
        }

    def setup_publisher(
            self,
            publisher: PublisherProto[IncomingMessage],
            **kwargs: Any,
    ) -> None:
        return super().setup_publisher(
            publisher,
            **(
                    {
                        "app_id": self.app_id,
                        "virtual_host": self.virtual_host,
                    }
                    | kwargs
            ),
        )

    @override
    async def connect(  # type: ignore[override]
            self,
            url: Annotated[
                Union[str, "URL", None],
                Doc("RabbitMQ destination location to connect."),
            ] = EMPTY,
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
                    "Security options to connect broker and generate AsyncAPI server security information.",
                ),
            ] = None,
            timeout: Annotated[
                "TimeoutType",
                Doc("Connection establishement timeout."),
            ] = None,
            fail_fast: Annotated[
                bool,
                Doc(
                    "Broker startup raises `AMQPConnectionError` if RabbitMQ is unreachable.",
                ),
            ] = EMPTY,
            reconnect_interval: Annotated[
                "TimeoutType",
                Doc("Time to sleep between reconnection attempts."),
            ] = EMPTY,
            # channel args
            channel_number: Annotated[
                Optional[int],
                Doc("Specify the channel number explicit."),
            ] = EMPTY,
            publisher_confirms: Annotated[
                bool,
                Doc(
                    "if `True` the `publish` method will "
                    "return `bool` type after publish is complete."
                    "Otherwise it will returns `None`.",
                ),
            ] = EMPTY,
            on_return_raises: Annotated[
                bool,
                Doc(
                    "raise an :class:`aio_pika.exceptions.DeliveryError`"
                    "when mandatory message will be returned",
                ),
            ] = EMPTY,
    ) -> "RobustConnection":
        """Connect broker object to RabbitMQ.

        To startup subscribers too you should use `broker.start()` after/instead this method.
        """
        kwargs: AnyDict = {}

        if channel_number is not EMPTY:
            kwargs["channel_number"] = channel_number

        if publisher_confirms is not EMPTY:
            kwargs["publisher_confirms"] = publisher_confirms

        if on_return_raises is not EMPTY:
            kwargs["on_return_raises"] = on_return_raises

        if timeout:
            kwargs["timeout"] = timeout

        if fail_fast is not EMPTY:
            kwargs["fail_fast"] = fail_fast

        if reconnect_interval is not EMPTY:
            kwargs["reconnect_interval"] = reconnect_interval

        url = None if url is EMPTY else url

        if any((
                url,
                host,
                port,
                virtualhost,
                ssl_options,
                client_properties,
                security,
        )):
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

        return await super().connect(**kwargs)

    @override
    async def _connect(  # type: ignore[override]
            self,
            url: str,
            *,
            fail_fast: bool,
            reconnect_interval: "TimeoutType",
            timeout: "TimeoutType",
            ssl_context: Optional["SSLContext"],
            # channel args
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
                reconnect_interval=reconnect_interval,
                fail_fast=fail_fast,
            ),
        )

        if self._channel is None:  # pragma: no branch
            channel = self._channel = cast(
                "RobustChannel",
                await connection.channel(
                    channel_number=channel_number,
                    publisher_confirms=publisher_confirms,
                    on_return_raises=on_return_raises,
                ),
            )

            if self._max_consumers:
                await channel.set_qos(prefetch_count=int(self._max_consumers))

            self.declarer.connect(connection=connection, channel=channel)
            await self.declarer.declare_queue(RABBIT_REPLY)

            self._producer.connect()

        return connection

    async def close(
            self,
            exc_type: Optional[type[BaseException]] = None,
            exc_val: Optional[BaseException] = None,
            exc_tb: Optional["TracebackType"] = None,
    ) -> None:
        await super().close(exc_type, exc_val, exc_tb)

        if self._channel is not None:
            if not self._channel.is_closed:
                await self._channel.close()

            self._channel = None

        if self._connection is not None:
            await self._connection.close()
            self._connection = None

        self.declarer.disconnect()
        self._producer.disconnect()

    async def start(self) -> None:
        """Connect broker to RabbitMQ and startup all subscribers."""
        await self.connect()
        self._setup()

        for publisher in self._publishers:
            if publisher.exchange is not None:
                await self.declare_exchange(publisher.exchange)

        await super().start()

        logger_state = self._state.get().logger_state
        if self._max_consumers:
            logger_state.log(f"Set max consumers to {self._max_consumers}")

    @override
    async def publish(
            self,
            message: "AioPikaSendableMessage" = None,
            queue: Union["RabbitQueue", str] = "",
            exchange: Union["RabbitExchange", str, None] = None,
            *,
            routing_key: str = "",
            # ↓ publish kwargs
            mandatory: bool = True,
            immediate: bool = False,
            timeout: "TimeoutType" = None,
            persist: bool = False,
            reply_to: Optional[str] = None,
            correlation_id: Optional[str] = None,
            # ↓ kwargs for super().init(), super is PublishCommand
            headers: Optional["HeadersType"] = None,
            content_type: Optional[str] = None,
            content_encoding: Optional[str] = None,
            expiration: Optional["DateType"] = None,
            message_id: Optional[str] = None,
            timestamp: Optional["DateType"] = None,
            message_type: Optional[str] = None,
            user_id: Optional[str] = None,
            priority: Optional[int] = None,
    ) -> Optional["aiormq.abc.ConfirmationFrameType"]:
        """Publish message directly.

        This method allows you to publish a message in a non-AsyncAPI-documented way. It can be used in other frameworks or to publish messages at specific intervals.

        Please, use @broker.publisher(...) or broker.publisher(...).publish(...) for the regular method of publishing.

        Args:
            message:
                The body of the message to send.
            queue:
                The routing key for the message. Used to determine where the message should be delivered.
            exchange:
                The target exchange to publish the message to. If None, the default exchange is used.
            routing_key:
                A key used for routing the message. Overrides the queue option if provided.
            mandatory:
                If set to True, the client waits for confirmation that the message is placed into a queue. If there is no suitable queue, RabbitMQ returns the message to the client.
            immediate:
                If set to True, the client expects a consumer ready to process the message. If no consumer is available, RabbitMQ returns the message to the client.
            timeout:
                The time in seconds to wait for confirmation from RabbitMQ that the message has been processed.
            persist:
                If set to True, the message will be restored if RabbitMQ is restarted.
            reply_to:
                The routing key for the reply message. This will always be sent to the default exchange.
            correlation_id:
                A manual identifier for the message, used for tracing.
            headers:
                Custom headers for the message to store metadata.
            content_type:
                The content type for the message body, such as application/json.
            content_encoding:
                The encoding of the message body (e.g., gzip).
            expiration:
                The lifetime of the message in seconds, or a datetime or timedelta.
            message_id:
                A custom ID for the message. If not provided, it will be automatically generated.
            timestamp:
                A timestamp for when the message is published. If not provided, it will be automatically generated.
            message_type:
                A type to specify the kind of message being sent (e.g., orders.created).
            user_id:
                The ID of the user sending the message, if required.
            priority:
                The priority of the message (0 by default).

        Returns:
            An optional aiormq.abc.ConfirmationFrameType representing the confirmation frame if RabbitMQ is configured to send confirmations.
        """
        cmd = RabbitPublishCommand(
            message,
            routing_key=routing_key or RabbitQueue.validate(queue).routing,
            exchange=RabbitExchange.validate(exchange),
            correlation_id=correlation_id or gen_cor_id(),
            app_id=self.app_id,
            mandatory=mandatory,
            immediate=immediate,
            persist=persist,
            reply_to=reply_to,
            headers=headers,
            content_type=content_type,
            content_encoding=content_encoding,
            expiration=expiration,
            message_id=message_id,
            message_type=message_type,
            timestamp=timestamp,
            user_id=user_id,
            timeout=timeout,
            priority=priority,
            _publish_type=PublishType.PUBLISH,
        )

        return await super()._basic_publish(cmd, producer=self._producer)

    @override
    async def request(  # type: ignore[override]
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
                    "Overrides `queue` option if presented.",
                ),
            ] = "",
            mandatory: Annotated[
                bool,
                Doc(
                    "Client waits for confirmation that the message is placed to some queue. "
                    "RabbitMQ returns message to client if there is no suitable queue.",
                ),
            ] = True,
            immediate: Annotated[
                bool,
                Doc(
                    "Client expects that there is consumer ready to take the message to work. "
                    "RabbitMQ returns message to client if there is no suitable consumer.",
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
            # message args
            correlation_id: Annotated[
                Optional[str],
                Doc(
                    "Manual message **correlation_id** setter. "
                    "**correlation_id** is a useful option to trace messages.",
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
                    "Will be set automatically if not specified.",
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
    ) -> "RabbitMessage":
        cmd = RabbitPublishCommand(
            message,
            routing_key=routing_key or RabbitQueue.validate(queue).routing,
            exchange=RabbitExchange.validate(exchange),
            correlation_id=correlation_id or gen_cor_id(),
            app_id=self.app_id,
            mandatory=mandatory,
            immediate=immediate,
            persist=persist,
            headers=headers,
            content_type=content_type,
            content_encoding=content_encoding,
            expiration=expiration,
            message_id=message_id,
            message_type=message_type,
            timestamp=timestamp,
            user_id=user_id,
            timeout=timeout,
            priority=priority,
            _publish_type=PublishType.REQUEST,
        )

        msg: RabbitMessage = await super()._basic_request(cmd, producer=self._producer)
        return msg

    async def declare_queue(
            self,
            queue: Annotated[
                "RabbitQueue",
                Doc("Queue object to create."),
            ],
    ) -> "RobustQueue":
        """Declares queue object in **RabbitMQ**."""
        return await self.declarer.declare_queue(queue)

    async def declare_exchange(
            self,
            exchange: Annotated[
                "RabbitExchange",
                Doc("Exchange object to create."),
            ],
    ) -> "RobustExchange":
        """Declares exchange object in **RabbitMQ**."""
        return await self.declarer.declare_exchange(exchange)

    @override
    async def ping(self, timeout: Optional[float]) -> bool:
        sleep_time = (timeout or 10) / 10

        with anyio.move_on_after(timeout) as cancel_scope:
            if self._connection is None:
                return False

            while True:
                if cancel_scope.cancel_called:
                    return False

                if self._connection.connected.is_set():
                    return True

                await anyio.sleep(sleep_time)

        return False
