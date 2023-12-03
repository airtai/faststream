from typing import Any, Callable, Optional, Sequence, Union

import aio_pika
from fast_depends.dependencies import Depends

from faststream._compat import override
from faststream.broker.core.asyncronous import default_filter
from faststream.broker.middlewares import BaseMiddleware
from faststream.broker.router import BrokerRouter
from faststream.broker.types import (
    CustomDecoder,
    CustomParser,
    Filter,
    P_HandlerParams,
    T_HandlerReturn,
)
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.rabbit.asyncapi import Publisher
from faststream.rabbit.message import RabbitMessage
from faststream.rabbit.shared.router import RabbitRoute
from faststream.rabbit.shared.schemas import RabbitExchange, RabbitQueue, ReplyConfig
from faststream.rabbit.shared.types import TimeoutType
from faststream.types import AnyDict

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
        parser: Optional[CustomParser[aio_pika.IncomingMessage, RabbitMessage]] = None,
        decoder: Optional[CustomDecoder[RabbitMessage]] = None,
        include_in_schema: bool = True,
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
        reply_config: Optional[ReplyConfig] = None,
        # broker arguments
        dependencies: Sequence[Depends] = (),
        filter: Filter[RabbitMessage] = default_filter,
        parser: Optional[CustomParser[aio_pika.IncomingMessage, RabbitMessage]] = None,
        decoder: Optional[CustomDecoder[RabbitMessage]] = None,
        middlewares: Optional[
            Sequence[
                Callable[
                    [aio_pika.IncomingMessage],
                    BaseMiddleware,
                ]
            ]
        ] = None,
        retry: Union[bool, int] = False,
        no_ack: bool = False,
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        include_in_schema: bool = True,
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
        schema: Optional[Any] = None,
        include_in_schema: bool = True,
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
