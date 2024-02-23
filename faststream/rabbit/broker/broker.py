from contextlib import AsyncExitStack
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

import aio_pika
from typing_extensions import override

from faststream.broker.core.broker import BrokerUsecase, default_filter
from faststream.broker.utils import get_watcher_context
from faststream.exceptions import NOT_CONNECTED_YET
from faststream.rabbit.asyncapi import Handler, Publisher
from faststream.rabbit.broker.logging import RabbitLoggingMixin
from faststream.rabbit.helpers import RabbitDeclarer, build_url
from faststream.rabbit.producer import AioPikaFastProducer
from faststream.rabbit.schemas.constants import RABBIT_REPLY
from faststream.rabbit.schemas.schemas import (
    RabbitExchange,
    RabbitQueue,
)
from faststream.rabbit.security import parse_security

if TYPE_CHECKING:
    from types import TracebackType

    import aiormq
    from aio_pika.abc import SSLOptions
    from fast_depends.dependencies import Depends
    from pamqp.common import FieldTable
    from yarl import URL

    from faststream.broker.core.handler_wrapper_mixin import WrapperProtocol
    from faststream.broker.types import (
        CustomDecoder,
        CustomParser,
        Filter,
        PublisherMiddleware,
        SubscriberMiddleware,
    )
    from faststream.rabbit.message import RabbitMessage
    from faststream.rabbit.schemas.schemas import ReplyConfig
    from faststream.rabbit.types import TimeoutType
    from faststream.security import BaseSecurity
    from faststream.types import AnyDict, DecodedMessage, SendableMessage


class RabbitBroker(
    RabbitLoggingMixin,
    BrokerUsecase["aio_pika.IncomingMessage", "aio_pika.RobustConnection"],
):
    url: str
    handlers: Dict[int, Handler]
    _publishers: Dict[int, Publisher]

    declarer: Optional[RabbitDeclarer]
    _producer: Optional[AioPikaFastProducer]
    _channel: Optional["aio_pika.RobustChannel"]

    def __init__(
        self,
        url: Union[str, "URL", None] = "amqp://guest:guest@localhost:5672/",
        *,
        # connection args
        host: Optional[str] = None,
        port: Optional[int] = None,
        login: Optional[str] = None,
        password: Optional[str] = None,
        virtualhost: Optional[str] = None,
        ssl_options: Optional["SSLOptions"] = None,
        client_properties: Optional["FieldTable"] = None,
        # broker args
        max_consumers: Optional[int] = None,
        protocol: Optional[str] = None,
        protocol_version: Optional[str] = "0.9.1",
        security: Optional["BaseSecurity"] = None,
        **kwargs: Any,
    ) -> None:
        security_args = parse_security(security)

        amqp_url = build_url(
            url,
            host=host,
            port=port,
            virtualhost=virtualhost,
            ssl_options=ssl_options,
            client_properties=client_properties,
            login=security_args.get("login", login),
            password=security_args.get("password", password),
            ssl=security_args.get("ssl", kwargs.pop("ssl", False)),
        )

        super().__init__(
            url=str(amqp_url),
            protocol_version=protocol_version,
            security=security,
            ssl_context=security_args.get("ssl_context", None),
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

    async def connect(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> "aio_pika.RobustConnection":
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
        ssl_options: Optional["SSLOptions"] = None,
        client_properties: Optional["FieldTable"] = None,
        **kwargs: Any,
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
                **kwargs,
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

    async def start(self) -> None:
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
        queue: Union[str, RabbitQueue],
        exchange: Union[str, RabbitExchange, None] = None,
        *,
        consume_args: Optional["AnyDict"] = None,
        reply_config: Optional["ReplyConfig"] = None,
        # broker arguments
        dependencies: Iterable["Depends"] = (),
        parser: Optional["CustomParser[aio_pika.IncomingMessage]"] = None,
        decoder: Optional["CustomDecoder[RabbitMessage]"] = None,
        middlewares: Iterable["SubscriberMiddleware"] = (),
        filter: "Filter[RabbitMessage]" = default_filter,
        retry: bool = False,
        no_ack: bool = False,
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        include_in_schema: bool = True,
        get_dependent: Optional[Any] = None,
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
        queue: Union[RabbitQueue, str] = "",
        exchange: Union[RabbitExchange, str, None] = None,
        *,
        routing_key: str = "",
        mandatory: bool = True,
        immediate: bool = False,
        timeout: "TimeoutType" = None,
        persist: bool = False,
        reply_to: Optional[str] = None,
        # specific
        middlewares: Iterable["PublisherMiddleware"] = (),
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        schema: Optional[Any] = None,
        include_in_schema: bool = True,
        priority: Optional[int] = None,
        **message_kwargs: Any,
    ) -> Publisher:
        q, ex = RabbitQueue.validate(queue), RabbitExchange.validate(exchange)

        publisher = Publisher(
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
        message: "SendableMessage" = None,
        *args: Any,
        **kwargs: Any,
    ) -> Union["aiormq.abc.ConfirmationFrameType", "DecodedMessage"]:
        assert self._producer, NOT_CONNECTED_YET  # nosec B101

        async with AsyncExitStack() as stack:
            for m in self.middlewares:
                message = await stack.enter_async_context(
                    m().publish_scope(message, *args, **kwargs)
                )

            return await self._producer.publish(message, *args, **kwargs)

    async def declare_queue(
        self,
        queue: RabbitQueue,
    ) -> "aio_pika.RobustQueue":
        assert self.declarer, NOT_CONNECTED_YET  # nosec B101
        return await self.declarer.declare_queue(queue)

    async def declare_exchange(
        self,
        exchange: RabbitExchange,
    ) -> "aio_pika.RobustExchange":
        assert self.declarer, NOT_CONNECTED_YET  # nosec B101
        return await self.declarer.declare_exchange(exchange)
