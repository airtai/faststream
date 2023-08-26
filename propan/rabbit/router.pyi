from typing import Any, Awaitable, Callable, Optional, Sequence, Union

import aio_pika
from fast_depends.dependencies import Depends

from propan._compat import override
from propan.broker.core.asyncronous import default_filter
from propan.broker.message import PropanMessage
from propan.broker.middlewares import BaseMiddleware
from propan.broker.router import BrokerRouter
from propan.broker.types import (
    AsyncCustomDecoder,
    AsyncCustomParser,
    P_HandlerParams,
    T_HandlerReturn,
)
from propan.broker.wrapper import HandlerCallWrapper
from propan.rabbit.asyncapi import Publisher
from propan.rabbit.shared.router import RabbitRoute
from propan.rabbit.shared.schemas import RabbitExchange, RabbitQueue
from propan.rabbit.shared.types import TimeoutType
from propan.types import AnyDict

RabbitMessage = PropanMessage[aio_pika.IncomingMessage]

class RabbitRouter(BrokerRouter[int, aio_pika.IncomingMessage]):
    def __init__(
        self,
        prefix: str = "",
        handlers: Sequence[RabbitRoute] = (),
        *,
        dependencies: Sequence[Depends] = (),
        middlewares: Optional[
            Sequence[Callable[[aio_pika.IncomingMessage], BaseMiddleware]]
        ] = None,
        parser: Optional[AsyncCustomParser[aio_pika.IncomingMessage]] = None,
        decoder: Optional[AsyncCustomDecoder[aio_pika.IncomingMessage]] = None,
    ): ...
    @staticmethod
    @override
    def _get_publisher_key(publisher: Publisher) -> int: ...  # type: ignore[override]
    @staticmethod
    @override
    def _update_publisher_prefix(  # type: ignore[override]
        prefix: str,
        publisher: Publisher,
    ) -> Publisher: ...
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
            Sequence[
                Callable[
                    [aio_pika.IncomingMessage],
                    BaseMiddleware,
                ]
            ]
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
