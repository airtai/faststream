from typing import Any, Callable, Sequence

import aio_pika
from fast_depends.dependencies import Depends
from typing_extensions import override

from faststream.broker.core.asynchronous import default_filter
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
        middlewares: Sequence[Callable[[aio_pika.IncomingMessage], BaseMiddleware]]
        | None = None,
        parser: CustomParser[aio_pika.IncomingMessage, RabbitMessage] | None = None,
        decoder: CustomDecoder[RabbitMessage] | None = None,
        include_in_schema: bool = True,
    ) -> None: ...
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
