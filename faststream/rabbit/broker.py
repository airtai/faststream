import warnings
from functools import partial, wraps
from types import TracebackType
from typing import (
    Any,
    AsyncContextManager,
    Awaitable,
    Callable,
    Dict,
    Optional,
    Sequence,
    Type,
    Union,
    cast,
)

import aio_pika
import aiormq
from aio_pika.abc import SSLOptions
from fast_depends.dependencies import Depends
from pamqp.common import FieldTable
from yarl import URL

from faststream._compat import model_to_dict, override
from faststream.broker.core.asyncronous import BrokerAsyncUsecase, default_filter
from faststream.broker.message import StreamMessage
from faststream.broker.middlewares import BaseMiddleware
from faststream.broker.types import (
    AsyncPublisherProtocol,
    CustomDecoder,
    CustomParser,
    Filter,
    P_HandlerParams,
    T_HandlerReturn,
    WrappedReturn,
)
from faststream.broker.wrapper import FakePublisher, HandlerCallWrapper
from faststream.exceptions import NOT_CONNECTED_YET
from faststream.rabbit.asyncapi import Handler, Publisher
from faststream.rabbit.helpers import RabbitDeclarer
from faststream.rabbit.message import RabbitMessage
from faststream.rabbit.producer import AioPikaFastProducer
from faststream.rabbit.security import parse_security
from faststream.rabbit.shared.constants import RABBIT_REPLY
from faststream.rabbit.shared.logging import RabbitLoggingMixin
from faststream.rabbit.shared.schemas import (
    RabbitExchange,
    RabbitQueue,
    ReplyConfig,
    get_routing_hash,
)
from faststream.rabbit.shared.types import TimeoutType
from faststream.rabbit.shared.utils import build_url
from faststream.security import BaseSecurity
from faststream.types import AnyDict, SendableMessage
from faststream.utils import context


class RabbitBroker(
    RabbitLoggingMixin,
    BrokerAsyncUsecase[aio_pika.IncomingMessage, aio_pika.RobustConnection],
):
    """
    A RabbitMQ broker for FastAPI applications.

    This class extends the base `BrokerAsyncUsecase` and provides asynchronous support for RabbitMQ as a message broker.

    Args:
        url (Union[str, URL, None], optional): The RabbitMQ connection URL. Defaults to "amqp://guest:guest@localhost:5672/".
        max_consumers (Optional[int], optional): Maximum number of consumers to limit message consumption. Defaults to None.
        protocol (str, optional): The protocol to use (e.g., "amqp"). Defaults to "amqp".
        protocol_version (Optional[str], optional): The protocol version to use (e.g., "0.9.1"). Defaults to "0.9.1".
        **kwargs: Additional keyword arguments.

    Attributes:
        handlers (Dict[int, Handler]): A dictionary of message handlers.
        _publishers (Dict[int, Publisher]): A dictionary of message publishers.
        declarer (Optional[RabbitDeclarer]): The RabbitMQ declarer instance.
        _producer (Optional[AioPikaFastProducer]): The RabbitMQ producer instance.
        _connection (Optional[aio_pika.RobustConnection]): The RabbitMQ connection instance.
        _channel (Optional[aio_pika.RobustChannel]): The RabbitMQ channel instance.
    """

    url: str
    handlers: Dict[int, Handler]
    _publishers: Dict[int, Publisher]

    declarer: Optional[RabbitDeclarer]
    _producer: Optional[AioPikaFastProducer]
    _connection: Optional[aio_pika.RobustConnection]
    _channel: Optional[aio_pika.RobustChannel]

    def __init__(
        self,
        url: Union[str, URL, None] = "amqp://guest:guest@localhost:5672/",
        *,
        # connection args
        host: Optional[str] = None,
        port: Optional[int] = None,
        login: Optional[str] = None,
        password: Optional[str] = None,
        virtualhost: Optional[str] = None,
        ssl_options: Optional[SSLOptions] = None,
        client_properties: Optional[FieldTable] = None,
        # broker args
        max_consumers: Optional[int] = None,
        protocol: Optional[str] = None,
        protocol_version: Optional[str] = "0.9.1",
        security: Optional[BaseSecurity] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the RabbitBroker.

        Args:
            url (Union[str, URL, None], optional): The RabbitMQ connection URL. Defaults to "amqp://guest:guest@localhost:5672/".
            max_consumers (Optional[int], optional): Maximum number of consumers to limit message consumption. Defaults to None.
            protocol (str, optional): The protocol to use (e.g., "amqp"). Defaults to "amqp".
            protocol_version (Optional[str], optional): The protocol version to use (e.g., "0.9.1"). Defaults to "0.9.1".
            **kwargs: Additional keyword arguments.
        """
        security_args = parse_security(security)

        if (ssl := kwargs.get("ssl")) or kwargs.get("ssl_context"):  # pragma: no cover
            warnings.warn(
                (
                    f"\nRabbitMQ {'`ssl`' if ssl else '`ssl_context`'} option was deprecated and will be removed in 0.4.0"
                    "\nPlease, use `security` with `BaseSecurity` or `SASLPlaintext` instead"
                ),
                DeprecationWarning,
                stacklevel=2,
            )

        amqp_url = build_url(
            url,
            host=host,
            port=port,
            login=security_args.get("login", login),
            password=security_args.get("password", password),
            virtualhost=virtualhost,
            ssl=security_args.get("ssl", kwargs.pop("ssl", False)),
            ssl_options=ssl_options,
            client_properties=client_properties,
        )

        super().__init__(
            url=str(amqp_url),
            protocol_version=protocol_version,
            security=security,
            ssl_context=security_args.get(
                "ssl_context", kwargs.pop("ssl_context", None)
            ),
            **kwargs,
        )

        # respect ascynapi_url argument scheme
        asyncapi_url = build_url(self.url)
        self.protocol = protocol or asyncapi_url.scheme
        self.virtual_host = asyncapi_url.path

        self._max_consumers = max_consumers

        self._channel = None
        self.declarer = None
        self._producer = None

    async def _close(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exec_tb: Optional[TracebackType] = None,
    ) -> None:
        """
        Close the RabbitMQ broker.

        Args:
            exc_type (Optional[Type[BaseException]], optional): The type of exception. Defaults to None.
            exc_val (Optional[BaseException], optional): The exception instance. Defaults to None.
            exec_tb (Optional[TracebackType], optional): The traceback. Defaults to None.
        """
        if self._channel is not None:
            await self._channel.close()
            self._channel = None

        self.declarer = None
        self._producer = None

        if self._connection is not None:  # pragma: no branch
            await self._connection.close()

        await super()._close(exc_type, exc_val, exec_tb)

    async def connect(self, *args: Any, **kwargs: Any) -> aio_pika.RobustConnection:
        """
        Connect to the RabbitMQ server.

        Args:
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            aio_pika.RobustConnection: The RabbitMQ connection instance.
        """
        connection = await super().connect(*args, **kwargs)
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
        ssl_options: Optional[SSLOptions] = None,
        client_properties: Optional[FieldTable] = None,
        **kwargs: Any,
    ) -> aio_pika.RobustConnection:
        """
        Connect to the RabbitMQ server.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            aio_pika.RobustConnection: The RabbitMQ connection instance.
        """
        connection = cast(
            aio_pika.RobustConnection,
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
                **kwargs,
            ),
        )

        if self._channel is None:  # pragma: no branch
            max_consumers = self._max_consumers
            channel = self._channel = cast(
                aio_pika.RobustChannel,
                await connection.channel(),
            )

            declarer = self.declarer = RabbitDeclarer(channel)
            self.declarer.queues[RABBIT_REPLY] = cast(
                aio_pika.RobustQueue,
                await channel.get_queue(RABBIT_REPLY, ensure=False),
            )

            self._producer = AioPikaFastProducer(
                channel,
                declarer,
                decoder=self._global_decoder,
                parser=self._global_parser,
            )

            if max_consumers:
                c = self._get_log_context(None, RabbitQueue(""), RabbitExchange(""))
                self._log(f"Set max consumers to {max_consumers}", extra=c)
                await channel.set_qos(prefetch_count=int(max_consumers))

        return connection

    async def start(self) -> None:
        """
        Start the RabbitMQ broker.

        Raises:
            RuntimeError: If the declarer is not initialized in the `connect` method.
        """
        context.set_global(
            "default_log_context",
            self._get_log_context(None, RabbitQueue(""), RabbitExchange("")),
        )

        await super().start()
        assert self.declarer, NOT_CONNECTED_YET  # nosec B101

        for publisher in self._publishers.values():
            if publisher.exchange is not None:
                await self.declare_exchange(publisher.exchange)

        for handler in self.handlers.values():
            c = self._get_log_context(None, handler.queue, handler.exchange)
            self._log(f"`{handler.call_name}` waiting for messages", extra=c)
            await handler.start(self.declarer)

    @override
    def subscriber(  # type: ignore[override]
        self,
        queue: Union[str, RabbitQueue],
        exchange: Union[str, RabbitExchange, None] = None,
        *,
        consume_args: Optional[AnyDict] = None,
        reply_config: Optional[ReplyConfig] = None,
        # broker arguments
        dependencies: Sequence[Depends] = (),
        parser: Optional[CustomParser[aio_pika.IncomingMessage, RabbitMessage]] = None,
        decoder: Optional[CustomDecoder[RabbitMessage]] = None,
        middlewares: Optional[
            Sequence[Callable[[aio_pika.IncomingMessage], BaseMiddleware]]
        ] = None,
        filter: Filter[RabbitMessage] = default_filter,
        no_ack: bool = False,
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        include_in_schema: bool = True,
        **original_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[aio_pika.IncomingMessage, P_HandlerParams, T_HandlerReturn],
    ]:
        """
        Decorator to define a message subscriber.

        Args:
            queue (Union[str, RabbitQueue]): The name of the RabbitMQ queue.
            exchange (Union[str, RabbitExchange, None], optional): The name of the RabbitMQ exchange. Defaults to None.
            consume_args (Optional[AnyDict], optional): Additional arguments for message consumption.
            no_ack (bool): Whether not to ack/nack/reject messages.
            title (Optional[str]): Title for AsyncAPI docs.
            description (Optional[str]): Description for AsyncAPI docs.

        Returns:
            Callable: A decorator function for defining message subscribers.
        """
        super().subscriber()

        r_queue = RabbitQueue.validate(queue)
        r_exchange = RabbitExchange.validate(exchange)

        self._setup_log_context(r_queue, r_exchange)

        key = get_routing_hash(r_queue, r_exchange)
        handler = self.handlers.get(
            key,
            Handler(
                log_context_builder=partial(
                    self._get_log_context, queue=r_queue, exchange=r_exchange
                ),
                queue=r_queue,
                exchange=r_exchange,
                consume_args=consume_args,
                description=description,
                title=title,
                virtual_host=self.virtual_host,
                include_in_schema=include_in_schema,
            ),
        )

        self.handlers[key] = handler

        def consumer_wrapper(
            func: Callable[P_HandlerParams, T_HandlerReturn],
        ) -> HandlerCallWrapper[
            aio_pika.IncomingMessage, P_HandlerParams, T_HandlerReturn
        ]:
            """Wraps a consumer function with additional functionality.

            Args:
                func: The consumer function to be wrapped.

            Returns:
                The wrapped consumer function.

            Raises:
                NotImplementedError: If silent animals are not supported.
            !!! note

                The above docstring is autogenerated by docstring-gen library (https://docstring-gen.airt.ai)
            """
            handler_call, dependant = self._wrap_handler(
                func,
                extra_dependencies=dependencies,
                no_ack=no_ack,
                _process_kwargs={
                    "reply_config": reply_config,
                },
                **original_kwargs,
            )

            handler.add_call(
                handler=handler_call,
                filter=filter,
                middlewares=middlewares,
                parser=parser or self._global_parser,
                decoder=decoder or self._global_decoder,
                dependant=dependant,
            )

            return handler_call

        return consumer_wrapper

    @override
    def publisher(  # type: ignore[override]
        self,
        queue: Union[RabbitQueue, str] = "",
        exchange: Union[RabbitExchange, str, None] = None,
        *,
        routing_key: str = "",
        mandatory: bool = True,
        immediate: bool = False,
        timeout: TimeoutType = None,
        persist: bool = False,
        reply_to: Optional[str] = None,
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        schema: Optional[Any] = None,
        include_in_schema: bool = True,
        priority: Optional[int] = None,
        **message_kwargs: Any,
    ) -> Publisher:
        """
        Define a message publisher.

        Args:
            queue (Union[RabbitQueue, str], optional): The name of the RabbitMQ queue. Defaults to "".
            exchange (Union[RabbitExchange, str, None], optional): The name of the RabbitMQ exchange. Defaults to None.
            routing_key (str, optional): The routing key for messages. Defaults to "".
            mandatory (bool, optional): Whether the message is mandatory. Defaults to True.
            immediate (bool, optional): Whether the message should be sent immediately. Defaults to False.
            timeout (TimeoutType, optional): Timeout for message publishing. Defaults to None.
            persist (bool, optional): Whether to persist messages. Defaults to False.
            reply_to (Optional[str], optional): The reply-to queue name. Defaults to None.
            title (Optional[str]): Title for AsyncAPI docs.
            description (Optional[str]): Description for AsyncAPI docs.
            **message_kwargs (Any): Additional message properties and content.

        Returns:
            Publisher: A message publisher instance.
        """
        q, ex = RabbitQueue.validate(queue), RabbitExchange.validate(exchange)

        publisher = Publisher(
            title=title,
            queue=q,
            exchange=ex,
            routing_key=routing_key,
            mandatory=mandatory,
            immediate=immediate,
            timeout=timeout,
            persist=persist,
            reply_to=reply_to,
            priority=priority,
            message_kwargs=message_kwargs,
            _description=description,
            _schema=schema,
            virtual_host=self.virtual_host,
            include_in_schema=include_in_schema,
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
        *args: Any,
        **kwargs: Any,
    ) -> Union[aiormq.abc.ConfirmationFrameType, SendableMessage]:
        """
        Publish a message to the RabbitMQ broker.

        Args:
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Union[aiormq.abc.ConfirmationFrameType, SendableMessage]: The confirmation frame or the response message.
        """
        assert self._producer, NOT_CONNECTED_YET  # nosec B101
        return await self._producer.publish(*args, **kwargs)

    def _process_message(
        self,
        func: Callable[
            [StreamMessage[aio_pika.IncomingMessage]], Awaitable[T_HandlerReturn]
        ],
        watcher: Callable[..., AsyncContextManager[None]],
        reply_config: Optional[ReplyConfig] = None,
        **kwargs: Any,
    ) -> Callable[
        [StreamMessage[aio_pika.IncomingMessage]],
        Awaitable[WrappedReturn[T_HandlerReturn]],
    ]:
        """
        Process a message using the provided handler function.

        Args:
            func (Callable): The handler function for processing the message.
            watcher (BaseWatcher): The message watcher for tracking message processing.
            disable_watcher: Whether to use watcher context.

        Returns:
            Callable: A wrapper function for processing messages.
        """
        if reply_config is None:
            reply_kwargs = {}
        else:
            reply_kwargs = model_to_dict(reply_config)

        @wraps(func)
        async def process_wrapper(
            message: RabbitMessage,
        ) -> WrappedReturn[T_HandlerReturn]:
            """Asynchronously process a message and wrap the return value.

            Args:
                message: The RabbitMessage to process.

            Returns:
                A tuple containing the return value of the handler function and an optional AsyncPublisherProtocol.

            Raises:
                AssertionError: If the code reaches an unreachable point.
            !!! note

                The above docstring is autogenerated by docstring-gen library (https://docstring-gen.airt.ai)
            """
            async with watcher(message):
                r = await func(message)

                pub_response: Optional[AsyncPublisherProtocol]
                if message.reply_to:
                    pub_response = FakePublisher(
                        partial(
                            self.publish,
                            routing_key=message.reply_to,
                            **reply_kwargs,
                        )
                    )
                else:
                    pub_response = None

                return r, pub_response

        return process_wrapper

    async def declare_queue(
        self,
        queue: RabbitQueue,
    ) -> aio_pika.RobustQueue:
        """
        Declare a RabbitMQ queue.

        Args:
            queue (RabbitQueue): The RabbitMQ queue to declare.

        Returns:
            aio_pika.RobustQueue: The declared RabbitMQ queue.

        Raises:
            RuntimeError: If the declarer is not initialized in the `connect` method.
        """
        assert self.declarer, NOT_CONNECTED_YET  # nosec B101
        return await self.declarer.declare_queue(queue)

    async def declare_exchange(
        self,
        exchange: RabbitExchange,
    ) -> aio_pika.RobustExchange:
        """
        Declare a RabbitMQ exchange.

        Args:
            exchange (RabbitExchange): The RabbitMQ exchange to declare.

        Returns:
            aio_pika.RobustExchange: The declared RabbitMQ exchange.

        Raises:
            RuntimeError: If the declarer is not initialized in the `connect` method.
        """
        assert self.declarer, NOT_CONNECTED_YET  # nosec B101
        return await self.declarer.declare_exchange(exchange)
