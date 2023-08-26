from functools import partial, wraps
from types import TracebackType
from typing import Any, Awaitable, Callable, Dict, Optional, Sequence, Type, Union, cast

import aio_pika
import aiormq
from fast_depends.dependencies import Depends
from yarl import URL

from propan._compat import override
from propan.broker.core.asyncronous import BrokerAsyncUsecase, default_filter
from propan.broker.message import PropanMessage
from propan.broker.middlewares import BaseMiddleware
from propan.broker.push_back_watcher import BaseWatcher, WatcherContext
from propan.broker.types import (
    AsyncCustomDecoder,
    AsyncCustomParser,
    AsyncPublisherProtocol,
    P_HandlerParams,
    T_HandlerReturn,
    WrappedReturn,
)
from propan.broker.wrapper import FakePublisher, HandlerCallWrapper
from propan.rabbit.asyncapi import Handler, Publisher
from propan.rabbit.helpers import RabbitDeclarer
from propan.rabbit.producer import AioPikaPropanProducer
from propan.rabbit.shared.constants import RABBIT_REPLY
from propan.rabbit.shared.logging import RabbitLoggingMixin
from propan.rabbit.shared.schemas import RabbitExchange, RabbitQueue, get_routing_hash
from propan.rabbit.shared.types import TimeoutType
from propan.types import AnyDict, SendableMessage
from propan.utils import context
from propan.utils.functions import to_async

RabbitMessage = PropanMessage[aio_pika.IncomingMessage]


class RabbitBroker(
    RabbitLoggingMixin,
    BrokerAsyncUsecase[aio_pika.IncomingMessage, aio_pika.RobustConnection],
):
    handlers: Dict[int, Handler]  # type: ignore[assignment]
    _publishers: Dict[int, Publisher]  # type: ignore[assignment]

    declarer: Optional[RabbitDeclarer]
    _producer: Optional[AioPikaPropanProducer]
    _connection: Optional[aio_pika.RobustConnection]
    _channel: Optional[aio_pika.RobustChannel]

    def __init__(
        self,
        url: Union[str, URL, None] = "amqp://guest:guest@localhost:5672/",
        *,
        max_consumers: Optional[int] = None,
        protocol: str = "amqp",
        protocol_version: Optional[str] = "0.9.1",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            url=url,
            protocol=protocol,
            protocol_version=protocol_version,
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
        connection = await super().connect(*args, **kwargs)
        for p in self._publishers.values():
            p._producer = self._producer
        return connection

    async def _connect(
        self,
        **kwargs: Any,
    ) -> aio_pika.RobustConnection:
        connection = cast(
            aio_pika.RobustConnection,
            await aio_pika.connect_robust(**kwargs),
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

            self._producer = AioPikaPropanProducer(
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
        context.set_local(
            "log_context",
            self._get_log_context(None, RabbitQueue(""), RabbitExchange("")),
        )

        await super().start()
        assert self.declarer, "Declarer should be initialized in `connect` method"

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
        parser: Optional[AsyncCustomParser[aio_pika.IncomingMessage]] = None,
        decoder: Optional[AsyncCustomDecoder[aio_pika.IncomingMessage]] = None,
        middlewares: Optional[
            Sequence[Callable[[aio_pika.IncomingMessage], BaseMiddleware]]
        ] = None,
        filter: Union[
            Callable[[RabbitMessage], bool], Callable[[RabbitMessage], Awaitable[bool]]
        ] = default_filter,
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        **original_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[aio_pika.IncomingMessage, P_HandlerParams, T_HandlerReturn],
    ]:
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
        if self._producer is None:
            raise ValueError("RabbitBroker channel is not started yet")
        return await self._producer.publish(*args, **kwargs)

    def _process_message(
        self,
        func: Callable[[RabbitMessage], Awaitable[T_HandlerReturn]],
        watcher: BaseWatcher,
    ) -> Callable[[RabbitMessage], Awaitable[WrappedReturn[T_HandlerReturn]],]:
        @wraps(func)
        async def process_wrapper(
            message: RabbitMessage,
        ) -> WrappedReturn[T_HandlerReturn]:
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
        assert self.declarer, "Declarer should be initialized in `connect` method"
        return await self.declarer.declare_queue(queue)

    async def declare_exchange(
        self,
        exchange: RabbitExchange,
    ) -> aio_pika.RobustExchange:
        assert self.declarer, "Declarer should be initialized in `connect` method"
        return await self.declarer.declare_exchange(exchange)
