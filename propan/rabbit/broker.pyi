import logging
from ssl import SSLContext
from types import TracebackType
from typing import Any, Awaitable, Callable, Dict, Optional, Sequence, Type, Union

import aio_pika
import aiormq
from fast_depends.dependencies import Depends
from pamqp.common import FieldTable
from yarl import URL

from propan._compat import override
from propan.asyncapi import schema as asyncapi
from propan.broker.core.asyncronous import BrokerAsyncUsecase, default_filter
from propan.broker.message import PropanMessage
from propan.broker.middlewares import BaseMiddleware
from propan.broker.push_back_watcher import BaseWatcher
from propan.broker.types import (
    AsyncCustomDecoder,
    AsyncCustomParser,
    P_HandlerParams,
    T_HandlerReturn,
    WrappedReturn,
)
from propan.broker.wrapper import HandlerCallWrapper
from propan.log import access_logger
from propan.rabbit.asyncapi import Handler, Publisher
from propan.rabbit.helpers import RabbitDeclarer
from propan.rabbit.producer import AioPikaPropanProducer
from propan.rabbit.shared.logging import RabbitLoggingMixin
from propan.rabbit.shared.schemas import RabbitExchange, RabbitQueue
from propan.rabbit.shared.types import TimeoutType
from propan.rabbit.types import AioPikaSendableMessage
from propan.types import AnyDict, SendableMessage

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
        # aio-pika args
        host: str = "localhost",
        port: int = 5672,
        login: str = "guest",
        password: str = "guest",
        virtualhost: str = "/",
        ssl: bool = False,
        ssl_options: Optional[aio_pika.abc.SSLOptions] = None,
        ssl_context: Optional[SSLContext] = None,
        timeout: aio_pika.abc.TimeoutType = None,
        client_properties: Optional[FieldTable] = None,
        # specific args
        max_consumers: Optional[int] = None,
        # broker args
        apply_types: bool = True,
        dependencies: Sequence[Depends] = (),
        decoder: Optional[AsyncCustomDecoder[aio_pika.IncomingMessage]] = None,
        parser: Optional[AsyncCustomParser[aio_pika.IncomingMessage]] = None,
        middlewares: Optional[
            Sequence[
                Callable[
                    [aio_pika.IncomingMessage],
                    BaseMiddleware,
                ]
            ]
        ] = None,
        # AsyncAPI args
        protocol: str = "amqp",
        protocol_version: Optional[str] = "0.9.1",
        description: Optional[str] = None,
        tags: Optional[Sequence[asyncapi.Tag]] = None,
        # logging args
        logger: Optional[logging.Logger] = access_logger,
        log_level: int = logging.INFO,
        log_fmt: Optional[str] = None,
    ) -> None: ...
    async def _close(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exec_tb: Optional[TracebackType] = None,
    ) -> None: ...
    async def connect(
        self,
        url: Union[str, URL, None] = None,
        host: str = "localhost",
        port: int = 5672,
        login: str = "guest",
        password: str = "guest",
        virtualhost: str = "/",
        ssl: bool = False,
        ssl_options: Optional[aio_pika.abc.SSLOptions] = None,
        ssl_context: Optional[SSLContext] = None,
        timeout: aio_pika.abc.TimeoutType = None,
        client_properties: Optional[FieldTable] = None,
    ) -> aio_pika.RobustConnection: ...
    @override
    async def _connect(  # type: ignore[override]
        self,
        *,
        url: Union[str, URL, None] = None,
        host: str = "localhost",
        port: int = 5672,
        login: str = "guest",
        password: str = "guest",
        virtualhost: str = "/",
        ssl: bool = False,
        ssl_options: Optional[aio_pika.abc.SSLOptions] = None,
        ssl_context: Optional[SSLContext] = None,
        timeout: aio_pika.abc.TimeoutType = None,
        client_properties: Optional[FieldTable] = None,
    ) -> aio_pika.RobustConnection: ...
    async def start(self) -> None: ...
    @override
    def subscriber(  # type: ignore[override]
        self,
        queue: Union[str, RabbitQueue],
        exchange: Union[str, RabbitExchange, None] = None,
        *,
        consume_args: Optional[AnyDict] = None,
        # broker arguments
        dependencies: Sequence[Depends] = (),
        filter: Union[
            Callable[[RabbitMessage], bool], Callable[[RabbitMessage], Awaitable[bool]]
        ] = default_filter,
        parser: Optional[AsyncCustomParser[aio_pika.IncomingMessage]] = None,
        decoder: Optional[AsyncCustomDecoder[aio_pika.IncomingMessage]] = None,
        middlewares: Optional[
            Sequence[Callable[[aio_pika.IncomingMessage], BaseMiddleware]]
        ] = None,
        retry: Union[bool, int] = False,
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        **__service_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[aio_pika.IncomingMessage, P_HandlerParams, T_HandlerReturn],
    ]: ...
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
        # message args
        headers: Optional[aio_pika.abc.HeadersType] = None,
        content_type: Optional[str] = None,
        content_encoding: Optional[str] = None,
        priority: Optional[int] = None,
        correlation_id: Optional[str] = None,
        expiration: Optional[aio_pika.abc.DateType] = None,
        message_id: Optional[str] = None,
        timestamp: Optional[aio_pika.abc.DateType] = None,
        type: Optional[str] = None,
        user_id: Optional[str] = None,
        app_id: Optional[str] = None,
    ) -> Publisher: ...
    @override
    async def publish(  # type: ignore[override]
        self,
        message: AioPikaSendableMessage = "",
        queue: Union[RabbitQueue, str] = "",
        exchange: Union[RabbitExchange, str, None] = None,
        *,
        routing_key: str = "",
        mandatory: bool = True,
        immediate: bool = False,
        timeout: TimeoutType = None,
        persist: bool = False,
        reply_to: Optional[str] = None,
        # rpc args
        rpc: bool = False,
        rpc_timeout: Optional[float] = 30.0,
        raise_timeout: bool = False,
        # message args
        headers: Optional[aio_pika.abc.HeadersType] = None,
        content_type: Optional[str] = None,
        content_encoding: Optional[str] = None,
        priority: Optional[int] = None,
        correlation_id: Optional[str] = None,
        expiration: Optional[aio_pika.abc.DateType] = None,
        message_id: Optional[str] = None,
        timestamp: Optional[aio_pika.abc.DateType] = None,
        type: Optional[str] = None,
        user_id: Optional[str] = None,
        app_id: Optional[str] = None,
    ) -> Union[aiormq.abc.ConfirmationFrameType, SendableMessage]: ...
    def _process_message(
        self,
        func: Callable[[RabbitMessage], Awaitable[T_HandlerReturn]],
        watcher: BaseWatcher,
    ) -> Callable[[RabbitMessage], Awaitable[WrappedReturn[T_HandlerReturn]],]: ...
    async def declare_queue(
        self,
        queue: RabbitQueue,
    ) -> aio_pika.RobustQueue: ...
    async def declare_exchange(
        self,
        exchange: RabbitExchange,
    ) -> aio_pika.RobustExchange: ...
