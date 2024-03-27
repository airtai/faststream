import logging
from contextlib import AsyncExitStack
from inspect import Parameter
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    Mapping,
    Optional,
    Type,
    Union,
    cast,
)
from urllib.parse import urlparse

from fast_depends.dependencies import Depends
from redis.asyncio.client import Redis
from redis.asyncio.connection import (
    Connection,
    ConnectionPool,
    DefaultParser,
    Encoder,
    parse_url,
)
from typing_extensions import Annotated, Doc, TypeAlias, deprecated, override

from faststream.__about__ import SERVICE_NAME, __version__
from faststream.broker.core.broker import BrokerUsecase, default_filter
from faststream.exceptions import NOT_CONNECTED_YET
from faststream.redis.asyncapi import Handler, HandlerType, Publisher, PublisherType
from faststream.redis.broker.logging import RedisLoggingMixin
from faststream.redis.producer import RedisFastProducer
from faststream.redis.schemas import ListSub, PubSub, StreamSub
from faststream.redis.security import parse_security

if TYPE_CHECKING:
    from types import TracebackType

    from fast_depends.dependencies import Depends
    from redis.asyncio.connection import BaseParser
    from typing_extensions import TypedDict, Unpack

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
    from faststream.security import BaseSecurity
    from faststream.types import AnyDict, DecodedMessage, SendableMessage

    class RedisInitKwargs(TypedDict, total=False):
        host: Optional[str]
        port: Union[str, int, None]
        db: Union[str, int, None]
        client_name: Optional[str]
        health_check_interval: Optional[float]
        max_connections: Optional[int]
        socket_timeout: Optional[float]
        socket_connect_timeout: Optional[float]
        socket_read_size: Optional[int]
        socket_keepalive: Optional[bool]
        socket_keepalive_options: Optional[Mapping[int, Union[int, bytes]]]
        socket_type: Optional[int]
        retry_on_timeout: Optional[bool]
        encoding: Optional[str]
        encoding_errors: Optional[str]
        decode_responses: Optional[bool]
        parser_class: Optional[Type["BaseParser"]]
        connection_class: Optional[Type["Connection"]]
        encoder_class: Optional[Type["Encoder"]]


Channel: TypeAlias = str


class RedisBroker(
    RedisLoggingMixin,
    BrokerUsecase["AnyDict", "Redis[bytes]"],
):
    """Redis broker."""

    url: str
    handlers: Dict[int, HandlerType]
    _publishers: Dict[int, PublisherType]

    _producer: Optional[RedisFastProducer]

    def __init__(
        self,
        url: str = "redis://localhost:6379",
        polling_interval: Optional[float] = None,
        *,
        host: str = "localhost",
        port: Union[str, int] = 6379,
        db: Union[str, int] = 0,
        client_name: Optional[str] = SERVICE_NAME,
        health_check_interval: float = 0,
        max_connections: Optional[int] = None,
        socket_timeout: Optional[float] = None,
        socket_connect_timeout: Optional[float] = None,
        socket_read_size: int = 65536,
        socket_keepalive: bool = False,
        socket_keepalive_options: Optional[Mapping[int,
                                                   Union[int, bytes]]] = None,
        socket_type: int = 0,
        retry_on_timeout: bool = False,
        encoding: str = "utf-8",
        encoding_errors: str = "strict",
        decode_responses: bool = False,
        parser_class: Type["BaseParser"] = DefaultParser,
        connection_class: Type["Connection"] = Connection,
        encoder_class: Type["Encoder"] = Encoder,
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
            Optional["CustomDecoder[StreamMessage[AnyDict]]"],
            Doc("Custom decoder object."),
        ] = None,
        parser: Annotated[
            Optional["CustomParser[AnyDict]"],
            Doc("Custom parser object."),
        ] = None,
        dependencies: Annotated[
            Iterable["Depends"],
            Doc("Dependencies to apply to all broker subscribers."),
        ] = (),
        middlewares: Annotated[
            Iterable["BrokerMiddleware[AnyDict]"],
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
        """Redis broker.

        Args:
            url : URL of the Redis server
            polling_interval : interval in seconds to poll the Redis server for new messages (default: None)
            protocol : protocol of the Redis server (default: None)
            protocol_version : protocol version of the Redis server (default: "custom")
            security : security settings for the Redis server (default: None)
            kwargs : additional keyword arguments
        """
        self.global_polling_interval = polling_interval
        self._producer = None

        if asyncapi_url is None:
            asyncapi_url = url

        if protocol is None:
            url_kwargs = urlparse(asyncapi_url)
            protocol = url_kwargs.scheme

        super().__init__(
            url=url,
            host=host,
            port=port,
            db=db,
            client_name=client_name,
            health_check_interval=health_check_interval,
            max_connections=max_connections,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
            socket_read_size=socket_read_size,
            socket_keepalive=socket_keepalive,
            socket_keepalive_options=socket_keepalive_options,
            socket_type=socket_type,
            retry_on_timeout=retry_on_timeout,
            encoding=encoding,
            encoding_errors=encoding_errors,
            decode_responses=decode_responses,
            parser_class=parser_class,
            connection_class=connection_class,
            encoder_class=encoder_class,
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
            protocol=protocol,
            protocol_version=protocol_version,
            security=security,
            tags=tags,
            # logging
            logger=logger,
            log_level=log_level,
            log_fmt=log_fmt,
        )

    @override
    async def connect(  # type: ignore[override]
        self,
        url: Union[str, None, object] =  Parameter.empty,
        **kwargs: "Unpack[RedisInitKwargs]",
    ) -> "Redis[bytes]":
        """Connect to the Redis server."""
        if url is not Parameter.empty:
            connect_kwargs: "AnyDict" = {
                "url": url,
                **kwargs,
            }
        else:
            connect_kwargs = {**kwargs}

        connection = await super().connect(**connect_kwargs)

        for p in self._publishers.values():
            p._producer = self._producer

        return connection

    @override
    async def _connect(  # type: ignore[override]
        self,
        url: str,
        *,
        host: str,
        port: Union[str, int],
        db: Union[str, int],
        client_name: Optional[str],
        health_check_interval: float,
        max_connections: Optional[int],
        socket_timeout: Optional[float],
        socket_connect_timeout: Optional[float],
        socket_read_size: int,
        socket_keepalive: bool,
        socket_keepalive_options: Optional[Mapping[int, Union[int, bytes]]],
        socket_type: int,
        retry_on_timeout: bool,
        encoding: str,
        encoding_errors: str,
        decode_responses: bool,
        parser_class: Type["BaseParser"],
        connection_class: Type["Connection"],
        encoder_class: Type["Encoder"],
    ) -> "Redis[bytes]":
        url_options: "AnyDict" = parse_url(url)
        url_options.update(
            {
                "host": host,
                "port": port,
                "db": db,
                "client_name": client_name,
                "health_check_interval": health_check_interval,
                "max_connections": max_connections,
                "socket_timeout": socket_timeout,
                "socket_connect_timeout": socket_connect_timeout,
                "socket_read_size": socket_read_size,
                "socket_keepalive": socket_keepalive,
                "socket_keepalive_options": socket_keepalive_options,
                "socket_type": socket_type,
                "retry_on_timeout": retry_on_timeout,
                "encoding": encoding,
                "encoding_errors": encoding_errors,
                "decode_responses": decode_responses,
                "parser_class": parser_class,
                "connection_class": connection_class,
                "encoder_class": encoder_class,
            }
        )
        url_options.update(parse_security(self.security))
        pool = ConnectionPool(
            **url_options,
            lib_name="faststream",
            lib_version=__version__,
        )

        client: Redis[bytes] = Redis.from_pool(pool)  # type: ignore[attr-defined]
        self._producer = RedisFastProducer(
            connection=client,
            parser=self._global_parser,  # type: ignore[arg-type]
            decoder=self._global_parser,  # type: ignore[arg-type]
        )
        return client

    async def _close(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exc_tb: Optional["TracebackType"] = None,
    ) -> None:
        if self._connection is not None:
            await self._connection.aclose()  # type: ignore[attr-defined]

        await super()._close(exc_type, exc_val, exc_tb)

    async def start(self) -> None:
        await super().start()

        assert self._producer and self._connection, NOT_CONNECTED_YET  # nosec B101

        # Setup log context before starting handlers
        for handler in self.handlers.values():
            self._setup_log_context(
                channel=handler.get_log_context(None).get("channel")
            )

        for handler in self.handlers.values():
            self._log(
                f"`{handler.call_name}` waiting for messages",
                extra=handler.get_log_context(None),
            )
            await handler.start(
                self._connection,
                producer=self._producer,
            )

    @override
    def subscriber(  # type: ignore[override]
        self,
        channel: Annotated[
            Union[Channel, PubSub, None],
            Doc("Redis PubSub object name to send message."),
        ] = None,
        *,
        list: Annotated[
            Union[Channel, ListSub, None],
            Doc("Redis List object name to send message."),
        ] = None,
        stream: Annotated[
            Union[Channel, StreamSub, None],
            Doc("Redis Stream object name to send message."),
        ] = None,
        # broker arguments
        dependencies: Annotated[
            Iterable["Depends"],
            Doc("Dependencies list (`[Depends(),]`) to apply to the subscriber."),
        ] = (),
        parser: Annotated[
            Optional["CustomParser[AnyDict]"],
            Doc(
                "Parser to map original **aio_pika.IncomingMessage** Msg to FastStream one."
            ),
        ] = None,
        decoder: Annotated[
            Optional["CustomDecoder[StreamMessage[Any]]"],
            Doc("Function to decode FastStream msg bytes body to python objects."),
        ] = None,
        middlewares: Annotated[
            Iterable["SubscriberMiddleware"],
            Doc("Subscriber middlewares to wrap incoming message processing."),
        ] = (),
        filter: Annotated[
            "Filter[StreamMessage[Any]]",
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
    ) -> "WrapperProtocol[AnyDict]":
        super().subscriber()

        handler = Handler.create(  # type: ignore[abstract]
            channel=PubSub.validate(channel),
            list=ListSub.validate(list),
            stream=StreamSub.validate(stream),
            # base options
            extra_context={},
            graceful_timeout=self.graceful_timeout,
            middlewares=self.middlewares,
            logger=self.logger,
            no_ack=no_ack,
            retry=retry,
            # AsyncAPI
            title_=title,
            description_=description,
            include_in_schema=include_in_schema,
        )

        key = hash(handler)
        handler = self.handlers[key] = self.handlers.get(key, handler)

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
        channel: Annotated[
            Union[Channel, PubSub, None],
            Doc("Redis PubSub object name to send message."),
        ] = None,
        list: Annotated[
            Union[Channel, ListSub, None],
            Doc("Redis List object name to send message."),
        ] = None,
        stream: Annotated[
            Union[Channel, StreamSub, None],
            Doc("Redis Stream object name to send message."),
        ] = None,
        headers: Annotated[
            Optional["AnyDict"],
            Doc(
                "Message headers to store metainformation. "
                "Can be overrided by `publish.headers` if specified."
            ),
        ] = None,
        reply_to: Annotated[
            str,
            Doc("Reply message destination PubSub object name."),
        ] = "",
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
        """
        publisher = cast(
            Publisher,
            self.add_publisher(
                publisher=Publisher.create(
                    channel=PubSub.validate(channel),
                    list=ListSub.validate(list),
                    stream=StreamSub.validate(stream),
                    headers=headers,
                    reply_to=reply_to,
                    middlewares=middlewares,
                    # AsyncAPI
                    title_=title,
                    description_=description,
                    schema_=schema,
                    include_in_schema=include_in_schema,
                ),
            ),
        )

        if self._producer is not None:
            publisher._producer = self._producer

        return publisher

    @override
    async def publish(  # type: ignore[override]
        self,
        message: Annotated[
            "SendableMessage",
            Doc("Message body to send."),
        ] = None,
        channel: Annotated[
            Optional[str],
            Doc("Redis PubSub object name to send message."),
        ] = None,
        reply_to: Annotated[
            str,
            Doc("Reply message destination PubSub object name."),
        ] = "",
        headers: Annotated[
            Optional["AnyDict"],
            Doc("Message headers to store metainformation."),
        ] = None,
        correlation_id: Annotated[
            Optional[str],
            Doc(
                "Manual message **correlation_id** setter. "
                "**correlation_id** is a useful option to trace messages."
            ),
        ] = None,
        *,
        list: Annotated[
            Optional[str],
            Doc("Redis List object name to send message."),
        ] = None,
        stream: Annotated[
            Optional[str],
            Doc("Redis Stream object name to send message."),
        ] = None,
        maxlen: Annotated[
            Optional[int],
            Doc(
                "Redis Stream maxlen publish option. "
                "Remove eldest message if maxlen exceeded."
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
    ) -> Optional["DecodedMessage"]:
        assert self._producer, NOT_CONNECTED_YET  # nosec B101

        async with AsyncExitStack() as stack:
            for m in self.middlewares:
                message = await stack.enter_async_context(
                    m(None).publish_scope(
                        message,
                        channel=channel,
                        list=list,
                        stream=stream,
                        maxlen=maxlen,
                        reply_to=reply_to,
                        headers=headers,
                        correlation_id=correlation_id,
                        rpc=rpc,
                        rpc_timeout=rpc_timeout,
                        raise_timeout=raise_timeout,
                    )
                )

            return await self._producer.publish(
                message,
                channel=channel,
                list=list,
                stream=stream,
                maxlen=maxlen,
                reply_to=reply_to,
                headers=headers,
                correlation_id=correlation_id,
                rpc=rpc,
                rpc_timeout=rpc_timeout,
                raise_timeout=raise_timeout,
            )

        return None

    async def publish_batch(
        self,
        *messages: Annotated[
            "SendableMessage",
            Doc("Messages bodies to send."),
        ],
        list: Annotated[
            str,
            Doc("Redis List object name to send messages."),
        ],
    ) -> None:
        """Publish multiple messages to Redis List by one request."""
        assert self._producer, NOT_CONNECTED_YET  # nosec B101

        async with AsyncExitStack() as stack:
            wrapped_messages = [
                await stack.enter_async_context(
                    middleware(None).publish_scope(msg, list=list)
                )
                for msg in messages
                for middleware in self.middlewares
            ] or messages

            return await self._producer.publish_batch(*wrapped_messages, list=list)

        return None
