from typing import Any, Callable, Sequence

import aio_pika
from fast_depends.dependencies import Depends

from faststream.broker.core.asynchronous import default_filter
from faststream.broker.middlewares import BaseMiddleware
from faststream.broker.types import (
    CustomDecoder,
    CustomParser,
    Filter,
    T_HandlerReturn,
)
from faststream.rabbit.message import RabbitMessage
from faststream.rabbit.shared.schemas import RabbitExchange, RabbitQueue
from faststream.types import AnyDict

class RabbitRoute:
    """Delayed `RabbitBroker.subscriber()` registration object."""

    def __init__(
        self,
        call: Callable[..., T_HandlerReturn],
        queue: str | RabbitQueue,
        exchange: str | RabbitExchange | None = None,
        *,
        consume_args: AnyDict | None = None,
        # broker arguments
        dependencies: Sequence[Depends] = (),
        filter: Filter[RabbitMessage] = default_filter,
        parser: CustomParser[aio_pika.IncomingMessage, RabbitMessage] | None = None,
        decoder: CustomDecoder[RabbitMessage] | None = None,
        middlewares: Sequence[Callable[[aio_pika.IncomingMessage], BaseMiddleware]]
        | None = None,
        retry: bool | int = False,
        # AsyncAPI information
        title: str | None = None,
        description: str | None = None,
        include_in_schema: bool = True,
        **__service_kwargs: Any,
    ) -> None: ...
