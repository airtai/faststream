from functools import partial, wraps
from types import TracebackType
from typing import Any, Awaitable, Callable, Dict, Optional, Sequence, Type, Union, cast

import aio_pika
import aiormq
from fast_depends.dependencies import Depends
from yarl import URL

from faststream._compat import override
from faststream.broker.core.asyncronous import BrokerAsyncUsecase, default_filter
from faststream.broker.message import StreamMessage
from faststream.broker.middlewares import BaseMiddleware
from faststream.broker.push_back_watcher import BaseWatcher, WatcherContext
from faststream.broker.security import BaseSecurity
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
    get_routing_hash,
)
from faststream.rabbit.shared.types import TimeoutType
from faststream.types import AnyDict, SendableMessage
from faststream.utils import context
from faststream.utils.functions import to_async


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

    handlers: Dict[int, Handler]  # type: ignore[assignment]
    _publishers: Dict[int, Publisher]  # type: ignore[assignment]

    declarer: Optional[RabbitDeclarer]
    _producer: Optional[AioPikaFastProducer]
    _connection: Optional[aio_pika.RobustConnection]
    _channel: Optional[aio_pika.RobustChannel]

    def __init__(
        self,
        url: Union[str, URL, None] = "amqp://guest:guest@localhost:5672/",
        *,
        max_consumers: Optional[int] = None,
        protocol: str = "amqp",
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
        super().__init__(
            url=url,
            protocol=protocol,
            protocol_version=protocol_version,
            security=security,
            **kwargs,
        )

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

        if self.declarer is not None:
            self.declarer = None

        if self._producer is not None:
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
            await aio_pika.connect_robust(**kwargs, **parse_security(self.security)),
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
        context.set_local(
            "log_context",
            self._get_log_context(None, RabbitQueue(""), RabbitExchange("")),
        )

        await super().start()
        assert (  # nosec B101
            self.declarer
        ), "Declarer should be initialized in `connect` method"

        for handler in self.handlers.values():
            c = self._get_log_context(None, handler.queue, handler.exchange)
            self._log(f"`{handler.name}` waiting for messages", extra=c)
            await handler.start(self.declarer)

    @override
    def subscriber(  # type: ignore[override]
        self,
        queue: Union[str, RabbitQueue],
        exchange: Union[str, RabbitExchange, None] = None,
        *,
        consume_args: Optional[AnyDict] = None,
        # broker arguments
        dependencies: Sequence[Depends] = (),
        parser: Optional[CustomParser[aio_pika.IncomingMessage]] = None,
        decoder: Optional[CustomDecoder[aio_pika.IncomingMessage]] = None,
        middlewares: Optional[
            Sequence[Callable[[aio_pika.IncomingMessage], BaseMiddleware]]
        ] = None,
        filter: Filter[RabbitMessage] = default_filter,
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
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
                queue=r_queue,
                exchange=r_exchange,
                consume_args=consume_args,
                description=description,
                title=title,
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
                **original_kwargs,
                queue=r_queue,
                exchange=r_exchange,
            )

            handler.add_call(
                handler=handler_call,
                filter=to_async(filter),
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
        key = get_routing_hash(q, ex)
        publisher = self._publishers.get(
            key,
            Publisher(
                title=title,
                queue=q,
                exchange=ex,
                routing_key=routing_key,
                mandatory=mandatory,
                immediate=immediate,
                timeout=timeout,
                persist=persist,
                reply_to=reply_to,
                message_kwargs=message_kwargs,
                _description=description,
            ),
        )
        super().publisher(key, publisher)
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

        assert self._producer, "RabbitBroker channel is not started yet"  # nosec B101
        return await self._producer.publish(*args, **kwargs)

    def _process_message(
        self,
        func: Callable[
            [StreamMessage[aio_pika.IncomingMessage]], Awaitable[T_HandlerReturn]
        ],
        watcher: BaseWatcher,
    ) -> Callable[
        [StreamMessage[aio_pika.IncomingMessage]],
        Awaitable[WrappedReturn[T_HandlerReturn]],
    ]:
        """
        Process a message using the provided handler function.

        Args:
            func (Callable): The handler function for processing the message.
            watcher (BaseWatcher): The message watcher for tracking message processing.

        Returns:
            Callable: A wrapper function for processing messages.
        """

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
            async with WatcherContext(watcher, message):
                r = await self._execute_handler(func, message)

                pub_response: Optional[AsyncPublisherProtocol]
                if message.reply_to:
                    pub_response = FakePublisher(
                        partial(self.publish, routing_key=message.reply_to)
                    )
                else:
                    pub_response = None

                return r, pub_response

            raise AssertionError("unreachable")

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
        assert (  # nosec B101
            self.declarer
        ), "Declarer should be initialized in `connect` method"
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
        assert (  # nosec B101
            self.declarer
        ), "Declarer should be initialized in `connect` method"
        return await self.declarer.declare_exchange(exchange)
