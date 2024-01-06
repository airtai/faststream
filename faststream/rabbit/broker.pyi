import logging
from ssl import SSLContext
from types import TracebackType
from typing import (
    Any,
    AsyncContextManager,
    Awaitable,
    Callable,
    Sequence,
)

import aio_pika
import aiormq
from fast_depends.dependencies import Depends
from pamqp.common import FieldTable
from typing_extensions import override
from yarl import URL

from faststream.asyncapi import schema as asyncapi
from faststream.broker.core.asynchronous import BrokerAsyncUsecase, default_filter
from faststream.broker.message import StreamMessage
from faststream.broker.middlewares import BaseMiddleware
from faststream.broker.types import (
    CustomDecoder,
    CustomParser,
    Filter,
    P_HandlerParams,
    T_HandlerReturn,
    WrappedReturn,
)
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.log import access_logger
from faststream.rabbit.asyncapi import Handler, Publisher
from faststream.rabbit.helpers import RabbitDeclarer
from faststream.rabbit.message import RabbitMessage
from faststream.rabbit.producer import AioPikaFastProducer
from faststream.rabbit.shared.logging import RabbitLoggingMixin
from faststream.rabbit.shared.schemas import RabbitExchange, RabbitQueue, ReplyConfig
from faststream.rabbit.shared.types import TimeoutType
from faststream.rabbit.types import AioPikaSendableMessage
from faststream.security import BaseSecurity
from faststream.types import AnyDict, SendableMessage

class RabbitBroker(
    RabbitLoggingMixin,
    BrokerAsyncUsecase[aio_pika.IncomingMessage, aio_pika.RobustConnection],
):
    handlers: dict[int, Handler]
    _publishers: dict[int, Publisher]

    declarer: RabbitDeclarer | None
    _producer: AioPikaFastProducer | None
    _connection: aio_pika.RobustConnection | None
    _channel: aio_pika.RobustChannel | None

    # nosemgrep: python.lang.security.audit.hardcoded-password-default-argument.hardcoded-password-default-argument
    def __init__(
        self,
        url: str
        | URL
        | None = "amqp://guest:guest@localhost:5672/",  # pragma: allowlist secret
        *,
        # aio-pika args
        host: str = "localhost",
        port: int = 5672,
        login: str = "guest",
        password: str = "guest",
        virtualhost: str = "/",
        ssl_options: aio_pika.abc.SSLOptions | None = None,
        timeout: aio_pika.abc.TimeoutType = None,
        client_properties: FieldTable | None = None,
        security: BaseSecurity | None = None,
        # specific args
        max_consumers: int | None = None,
        graceful_timeout: float | None = None,
        # broker args
        apply_types: bool = True,
        validate: bool = True,
        dependencies: Sequence[Depends] = (),
        decoder: CustomDecoder[RabbitMessage] | None = None,
        parser: CustomParser[aio_pika.IncomingMessage, RabbitMessage] | None = None,
        middlewares: Sequence[Callable[[aio_pika.IncomingMessage], BaseMiddleware]]
        | None = None,
        # AsyncAPI args
        asyncapi_url: str | None = None,
        protocol: str = "amqp",
        protocol_version: str | None = "0.9.1",
        description: str | None = None,
        tags: Sequence[asyncapi.Tag] | None = None,
        # logging args
        logger: logging.Logger | None = access_logger,
        log_level: int = logging.INFO,
        log_fmt: str | None = None,
    ) -> None: ...
    async def _close(
        self,
        exc_type: type[BaseException] | None = None,
        exc_val: BaseException | None = None,
        exec_tb: TracebackType | None = None,
    ) -> None: ...
    # nosemgrep: python.lang.security.audit.hardcoded-password-default-argument.hardcoded-password-default-argument
    async def connect(
        self,
        url: str | URL | None = None,
        host: str = "localhost",
        port: int = 5672,
        login: str = "guest",
        password: str = "guest",
        virtualhost: str = "/",
        ssl_options: aio_pika.abc.SSLOptions | None = None,
        timeout: aio_pika.abc.TimeoutType = None,
        client_properties: FieldTable | None = None,
        security: BaseSecurity | None = None,
    ) -> aio_pika.RobustConnection: ...
    # nosemgrep: python.lang.security.audit.hardcoded-password-default-argument.hardcoded-password-default-argument
    @override
    async def _connect(  # type: ignore[override]
        self,
        *,
        url: str | URL | None = None,
        host: str = "localhost",
        port: int = 5672,
        login: str = "guest",
        password: str = "guest",
        virtualhost: str = "/",
        ssl: bool = False,
        ssl_options: aio_pika.abc.SSLOptions | None = None,
        ssl_context: SSLContext | None = None,
        timeout: aio_pika.abc.TimeoutType = None,
        client_properties: FieldTable | None = None,
    ) -> aio_pika.RobustConnection: ...
    async def start(self) -> None: ...
    @override
    def subscriber(  # type: ignore[override]
        self,
        queue: str | RabbitQueue,
        exchange: str | RabbitExchange | None = None,
        *,
        consume_args: AnyDict | None = None,
        reply_config: ReplyConfig | None = None,
        # broker arguments
        dependencies: Sequence[Depends] = (),
        filter: Filter[RabbitMessage] = default_filter,
        parser: CustomParser[aio_pika.IncomingMessage, RabbitMessage] | None = None,
        decoder: CustomDecoder[RabbitMessage] | None = None,
        middlewares: Sequence[Callable[[aio_pika.IncomingMessage], BaseMiddleware]]
        | None = None,
        retry: bool | int = False,
        no_ack: bool = False,
        # AsyncAPI information
        title: str | None = None,
        description: str | None = None,
        include_in_schema: bool = True,
        **__service_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[aio_pika.IncomingMessage, P_HandlerParams, T_HandlerReturn],
    ]: ...
    @override
    def publisher(  # type: ignore[override]
        self,
        queue: RabbitQueue | str = "",
        exchange: RabbitExchange | str | None = None,
        *,
        routing_key: str = "",
        mandatory: bool = True,
        immediate: bool = False,
        timeout: TimeoutType = None,
        persist: bool = False,
        reply_to: str | None = None,
        # AsyncAPI information
        title: str | None = None,
        description: str | None = None,
        schema: Any | None = None,
        include_in_schema: bool = True,
        # message args
        headers: aio_pika.abc.HeadersType | None = None,
        content_type: str | None = None,
        content_encoding: str | None = None,
        priority: int | None = None,
        correlation_id: str | None = None,
        expiration: aio_pika.abc.DateType | None = None,
        message_id: str | None = None,
        timestamp: aio_pika.abc.DateType | None = None,
        type: str | None = None,
        user_id: str | None = None,
        app_id: str | None = None,
    ) -> Publisher: ...
    @override
    async def publish(  # type: ignore[override]
        self,
        message: AioPikaSendableMessage = "",
        queue: RabbitQueue | str = "",
        exchange: RabbitExchange | str | None = None,
        *,
        routing_key: str = "",
        mandatory: bool = True,
        immediate: bool = False,
        timeout: TimeoutType = None,
        persist: bool = False,
        reply_to: str | None = None,
        # rpc args
        rpc: bool = False,
        rpc_timeout: float | None = 30.0,
        raise_timeout: bool = False,
        # message args
        headers: aio_pika.abc.HeadersType | None = None,
        content_type: str | None = None,
        content_encoding: str | None = None,
        priority: int | None = None,
        correlation_id: str | None = None,
        expiration: aio_pika.abc.DateType | None = None,
        message_id: str | None = None,
        timestamp: aio_pika.abc.DateType | None = None,
        type: str | None = None,
        user_id: str | None = None,
        app_id: str | None = None,
    ) -> aiormq.abc.ConfirmationFrameType | SendableMessage: ...
    def _process_message(
        self,
        func: Callable[
            [StreamMessage[aio_pika.IncomingMessage]], Awaitable[T_HandlerReturn]
        ],
        watcher: Callable[..., AsyncContextManager[None]],
        reply_config: ReplyConfig | None = None,
        **kwargs: Any,
    ) -> Callable[
        [StreamMessage[aio_pika.IncomingMessage]],
        Awaitable[WrappedReturn[T_HandlerReturn]],
    ]: ...
    async def declare_queue(
        self,
        queue: RabbitQueue,
    ) -> aio_pika.RobustQueue: ...
    async def declare_exchange(
        self,
        exchange: RabbitExchange,
    ) -> aio_pika.RobustExchange: ...
