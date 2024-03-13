import logging
from contextlib import AsyncExitStack
from inspect import Parameter
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    Optional,
    Type,
    Union,
    cast,
)
from urllib.parse import urlparse

import aio_pika
from typing_extensions import Annotated, Doc, deprecated, override

from faststream.__about__ import __version__
from faststream.broker.core.broker import BrokerUsecase, default_filter
from faststream.broker.utils import get_watcher_context
from faststream.exceptions import NOT_CONNECTED_YET
from faststream.rabbit.asyncapi import Handler, Publisher
from faststream.rabbit.broker.logging import RabbitLoggingMixin
from faststream.rabbit.helpers import RabbitDeclarer, build_url
from faststream.rabbit.producer import AioPikaFastProducer
from faststream.rabbit.publisher import PublishKwargs
from faststream.rabbit.schemas.constants import RABBIT_REPLY
from faststream.rabbit.schemas.schemas import (
    RabbitExchange,
    RabbitQueue,
)
from faststream.rabbit.security import parse_security

if TYPE_CHECKING:
    from ssl import SSLContext
    from types import TracebackType

    import aiormq
    from aio_pika.abc import SSLOptions, TimeoutType
    from fast_depends.dependencies import Depends
    from pamqp.common import FieldTable
    from yarl import URL

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
    from faststream.rabbit.message import RabbitMessage
    from faststream.rabbit.router import RabbitRouter
    from faststream.rabbit.schemas.schemas import ReplyConfig
    from faststream.rabbit.types import AioPikaSendableMessage
    from faststream.security import BaseSecurity
    from faststream.types import AnyDict, DecodedMessage


class RabbitBroker(
    RabbitLoggingMixin,
    BrokerUsecase[aio_pika.IncomingMessage, aio_pika.RobustConnection],
):
    """A class to represent a RabbitMQ broker."""

    url: str
    handlers: Dict[int, Handler]
    _publishers: Dict[int, Publisher]

    declarer: Optional[RabbitDeclarer]
    _producer: Optional[AioPikaFastProducer]
    _channel: Optional["aio_pika.RobustChannel"]

    def __init__(
        self,
        url: Annotated[
            Union[str, "URL", None],
            Doc("RabbitMQ destination location to connect."),
        ] = "amqp://guest:guest@localhost:5672/",
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
            aio_pika.abc.TimeoutType,
            Doc("Connection establishement timeout."),
        ] = None,
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
        ] = f"faststream-{__version__}",
        # broker base args
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
            Optional["CustomDecoder[StreamMessage[aio_pika.IncomingMessag]]"],
            Doc("Custom decoder object."),
        ] = None,
        parser: Annotated[
            Optional["CustomParser[aio_pika.IncomingMessag]"],
            Doc("Custom parser object."),
        ] = None,
        dependencies: Annotated[
            Iterable["Depends"],
            Doc("Dependencies to apply to all broker subscribers."),
        ] = (),
        middlewares: Annotated[
            Iterable["BrokerMiddleware[aio_pika.IncomingMessag]"],
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
        """Initialize the RabbitBroker object."""
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
            # Basic args
            # broker base
            graceful_timeout=graceful_timeout,
            apply_types=apply_types,
            validate=validate,
            dependencies=dependencies,
            decoder=decoder,
            parser=parser,
            middlewares=middlewares,
            # AsyncAPI
            description=description,
            asyncapi_url=asyncapi_url,
            protocol=protocol or builded_asyncapi_url.scheme,
            protocol_version=protocol_version,
            security=security,
            tags=tags,
            # logging
            logger=logger,
            log_level=log_level,
            log_fmt=log_fmt,
        )

        self._max_consumers = max_consumers

        self.app_id = app_id

        self._channel = None
        self.declarer = None
        self._producer = None

    async def connect(
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
            aio_pika.abc.TimeoutType,
            Doc("Connection establishement timeout."),
        ] = None,
    ) -> "aio_pika.RobustConnection":
        """Connect broker object to RabbitMQ.

        To startup subscribers too you should use `broker.start()` after/instead this method.
        """
        kwargs: AnyDict = {}

        if timeout:
            kwargs["timeout"] = timeout

        if url is not Parameter.empty or any(
            (host, port, virtualhost, ssl_options, client_properties, security)
        ):
            security_args = parse_security(security)

            kwargs["url"] = build_url(
                None if url is Parameter.empty else url,
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

        for p in self._publishers.values():
            p._producer = self._producer

        return connection

    async def _connect(
        self,
        url: str,
        *,
        host: Optional[str] = None,
        port: Optional[int] = None,
        login: Optional[str] = None,
        password: Optional[str] = None,
        virtualhost: Optional[str] = None,
        ssl_options: Optional["SSLOptions"] = None,
        client_properties: Optional["FieldTable"] = None,
        timeout: aio_pika.abc.TimeoutType = None,
        ssl_context: Optional["SSLContext"] = None,
    ) -> "aio_pika.RobustConnection":
        connection = cast(
            "aio_pika.RobustConnection",
            await aio_pika.connect_robust(
                build_url(
                    url,
                    host=host,
                    port=port,
                    login=login,
                    password=password,
                    virtualhost=virtualhost,
                    ssl_options=ssl_options,
                    client_properties=client_properties,
                ),
                timeout=timeout,
                ssl_context=ssl_context,
            ),
        )

        if self._channel is None:  # pragma: no branch
            max_consumers = self._max_consumers
            channel = self._channel = cast(
                "aio_pika.RobustChannel",
                await connection.channel(),
            )

            declarer = self.declarer = RabbitDeclarer(channel)
            self.declarer.queues[RABBIT_REPLY] = cast(
                "aio_pika.RobustQueue",
                await channel.get_queue(RABBIT_REPLY, ensure=False),
            )

            self._producer = AioPikaFastProducer(
                channel,
                declarer,
                decoder=self._global_decoder,
                parser=self._global_parser,
            )

            if max_consumers:
                c = Handler.build_log_context(None, RabbitQueue(""), RabbitExchange(""))
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

        if self._connection is not None:  # pragma: no branch
            await self._connection.close()

        await super()._close(exc_type, exc_val, exc_tb)

    def include_router(
        self,
        router: Annotated[
            "RabbitRouter",
            Doc(
                "`faststream.rabbit.RabbitRouter` object to copy publishers and subscribers from."
            ),
        ],
    ) -> None:
        for p in router._publishers.values():
            p.virtual_host = self.virtual_host
            p.app_id = self.app_id

        return super().include_router(router)

    async def start(self) -> None:
        """Connect broker to RabbitMQ cluster and startup all subscribers."""
        await super().start()

        assert self.declarer, NOT_CONNECTED_YET  # nosec B101

        for publisher in self._publishers.values():
            if publisher.exchange is not None:
                await self.declare_exchange(publisher.exchange)

        for handler in self.handlers.values():
            c = handler.get_log_context(None)
            self._log(f"`{handler.call_name}` waiting for messages", extra=c)
            await handler.start(self.declarer, self._producer)

    @override
    def subscriber(  # type: ignore[override]
        self,
        queue: Annotated[
            Union[str, RabbitQueue],
            Doc(
                "RabbitMQ queue to listen. "
                "**FastStream** declares and binds queue object to `exchange` automatically if it is not passive (by default)."
            ),
        ],
        exchange: Annotated[
            Union[str, RabbitExchange, None],
            Doc(
                "RabbitMQ exchange to bind queue to. "
                "Uses default exchange if not presented. "
                "**FastStream** declares exchange object automatically if it is not passive (by default)."
            ),
        ] = None,
        *,
        consume_args: Annotated[
            Optional["AnyDict"],
            Doc("Extra consumer arguments to use in `queue.consume(...)` method."),
        ] = None,
        reply_config: Annotated[
            Optional["ReplyConfig"],
            Doc("Extra options to use at replies publishing."),
        ] = None,
        # broker arguments
        dependencies: Annotated[
            Iterable["Depends"],
            Doc("Dependencies list (`[Depends(),]`) to apply to the subscriber."),
        ] = (),
        parser: Annotated[
            Optional["CustomParser[aio_pika.IncomingMessage]"],
            Doc(
                "Parser to map original **aio_pika.IncomingMessage** Msg to FastStream one."
            ),
        ] = None,
        decoder: Annotated[
            Optional["CustomDecoder[RabbitMessage]"],
            Doc("Function to decode FastStream msg bytes body to python objects."),
        ] = None,
        middlewares: Annotated[
            Iterable["SubscriberMiddleware"],
            Doc("Subscriber middlewares to wrap incoming message processing."),
        ] = (),
        filter: Annotated[
            "Filter[RabbitMessage]",
            Doc(
                "Overload subscriber to consume various messages from the same source."
            ),
            deprecated(
                "Deprecated in **FastStream 0.5.0**. "
                "Please, create `subscriber` object and use it explicitly instead. "
                "Argument will be removed in **FastStream 0.6.0**."
            ),
        ] = default_filter,
        retry: Annotated[
            Union[bool, int],
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
    ) -> "WrapperProtocol[aio_pika.IncomingMessage]":
        super().subscriber()

        r_queue = RabbitQueue.validate(queue)
        r_exchange = RabbitExchange.validate(exchange)

        self._setup_log_context(r_queue, r_exchange)

        key = Handler.get_routing_hash(r_queue, r_exchange)
        handler = self.handlers[key] = self.handlers.get(key) or Handler(
            queue=r_queue,
            exchange=r_exchange,
            consume_args=consume_args,
            # base options
            reply_config=reply_config,
            middlewares=self.middlewares,
            watcher=get_watcher_context(self.logger, no_ack, retry),
            graceful_timeout=self.graceful_timeout,
            extra_context={},
            # AsyncAPI
            app_id=self.app_id,
            title_=title,
            description_=description,
            virtual_host=self.virtual_host,
            include_in_schema=include_in_schema,
        )

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
        queue: Annotated[
            Union[RabbitQueue, str],
            Doc("Default message routing key to publish with."),
        ] = "",
        exchange: Annotated[
            Union[RabbitExchange, str, None],
            Doc("Target exchange to publish message to."),
        ] = None,
        *,
        routing_key: Annotated[
            str,
            Doc(
                "Default message routing key to publish with. "
                "Overrides `queue` option if presented."
            ),
        ] = "",
        mandatory: Annotated[
            bool,
            Doc(
                "Client waits for confimation that the message is placed to some queue. "
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
        priority: Annotated[
            Optional[int],
            Doc("The message priority (0 by default)."),
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
        # message args
        headers: Annotated[
            Optional[aio_pika.abc.HeadersType],
            Doc(
                "Message headers to store metainformation. "
                "Can be overrided by `publish.headers` if specified."
            ),
        ] = None,
        content_type: Annotated[
            Optional[str],
            Doc(
                "Message **content-type** header. "
                "Used by application, not core RabbitMQ. "
                "Will be setted automatically if not specified."
            ),
        ] = None,
        content_encoding: Annotated[
            Optional[str],
            Doc("Message body content encoding, e.g. **gzip**."),
        ] = None,
        expiration: Annotated[
            Optional[aio_pika.abc.DateType],
            Doc("Message expiration (lifetime) in seconds (or datetime or timedelta)."),
        ] = None,
        message_type: Annotated[
            Optional[str],
            Doc("Application-specific message type, e.g. **orders.created**."),
        ] = None,
        user_id: Annotated[
            Optional[str],
            Doc("Publisher connection User ID, validated if set."),
        ] = None,
    ) -> Publisher:
        """Creates long-living and **AsyncAPI**-documented publisher object.

        Usage::
          @broker.subscriber("in")  # should be decorated by subscriber too
          @broker.publisher("out1")
          @broker.publisher("out2")
          async def handler() -> str:
              '''You can use it as a handler decorator.'''
              return "Hi!"  # publishes result to "out1" and "out2"


          # or you can create publisher object and use it lately
          publisher = broker.publisher("out")
          ...
          await publisher.publish("Some message")

        References:
        You can find detail information about message properties here: https://www.rabbitmq.com/docs/publishers#message-properties
        """
        q, ex = RabbitQueue.validate(queue), RabbitExchange.validate(exchange)

        message_kwargs = PublishKwargs(
            mandatory=mandatory,
            immediate=immediate,
            timeout=timeout,
            persist=persist,
            reply_to=reply_to,
            headers=headers,
            priority=priority,
            content_type=content_type,
            content_encoding=content_encoding,
            message_type=message_type,
            user_id=user_id,
            expiration=expiration,
        )

        publisher = Publisher(
            queue=q,
            exchange=ex,
            routing_key=routing_key,
            message_kwargs=message_kwargs,
            app_id=self.app_id,
            # Specific
            middlewares=middlewares,
            # AsyncAPI
            title_=title,
            description_=description,
            schema_=schema,
            include_in_schema=include_in_schema,
            virtual_host=self.virtual_host,
        )

        key = publisher._get_routing_hash()
        publisher = self._publishers.get(key, publisher)
        super().publisher(key, publisher)
        if self._producer is not None:
            publisher._producer = self._producer
        return publisher

    @override
    async def publish(  # type: ignore[override]
        self,
        message: "AioPikaSendableMessage" = None,
        queue: Annotated[
            Union[RabbitQueue, str],
            Doc("Message routing key to publish with."),
        ] = "",
        exchange: Annotated[
            Union[RabbitExchange, str, None],
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
                "Client waits for confimation that the message is placed to some queue. "
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
            Optional[aio_pika.abc.HeadersType],
            Doc(
                "Message headers to store metainformation. "
                "Can be overrided by `publish.headers` if specified."
            ),
        ] = None,
        content_type: Annotated[
            Optional[str],
            Doc(
                "Message **content-type** header. "
                "Used by application, not core RabbitMQ. "
                "Will be setted automatically if not specified."
            ),
        ] = None,
        content_encoding: Annotated[
            Optional[str],
            Doc("Message body content encoding, e.g. **gzip**."),
        ] = None,
        expiration: Annotated[
            Optional[aio_pika.abc.DateType],
            Doc("Message expiration (lifetime) in seconds (or datetime or timedelta)."),
        ] = None,
        message_id: Annotated[
            Optional[str],
            Doc("Arbitrary message id. Generated automatically if not presented."),
        ] = None,
        timestamp: Annotated[
            Optional[aio_pika.abc.DateType],
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
    ) -> Union["aiormq.abc.ConfirmationFrameType", "DecodedMessage"]:
        """Publish message directly.

        This method allows you to publish message in not AsyncAPI-documented way. You can use it in another frameworks
        applications or to publish messages from time to time.

        Please, use `@broker.publisher(...)` or `broker.publisher(...).publish(...)` instead in a regular way.
        """
        assert self._producer, NOT_CONNECTED_YET  # nosec B101

        kwargs = {
            "routing_key": routing_key or RabbitQueue.validate(queue).routing,
            "exchange": exchange,
            "mandatory": mandatory,
            "immediate": immediate,
            "timeout": timeout,
            "persist": persist,
            "reply_to": reply_to,
            "headers": headers,
            "correlation_id": correlation_id,
            "content_type": content_type,
            "content_encoding": content_encoding,
            "expiration": expiration,
            "message_id": message_id,
            "timestamp": timestamp,
            "message_type": message_type,
            "user_id": user_id,
            "priority": priority,
            "app_id": self.app_id,
            # specific args
            "rpc": rpc,
            "rpc_timeout": rpc_timeout,
            "raise_timeout": raise_timeout,
        }

        async with AsyncExitStack() as stack:
            for m in self.middlewares:
                message = await stack.enter_async_context(
                    m(None).publish_scope(message, **kwargs)
                )

            return await self._producer.publish(message, **kwargs)

    async def declare_queue(
        self,
        queue: Annotated[
            RabbitQueue,
            Doc("Queue object to create."),
        ],
    ) -> "aio_pika.RobustQueue":
        """Declares queue object in RabbitMQ."""
        assert self.declarer, NOT_CONNECTED_YET  # nosec B101
        return await self.declarer.declare_queue(queue)

    async def declare_exchange(
        self,
        exchange: Annotated[
            RabbitExchange,
            Doc("Exchange object to create."),
        ],
    ) -> "aio_pika.RobustExchange":
        """Declares exchange object in RabbitMQ."""
        assert self.declarer, NOT_CONNECTED_YET  # nosec B101
        return await self.declarer.declare_exchange(exchange)
