from typing import Any, Callable, Optional, Sequence, Union

import aio_pika
from fast_depends.dependencies import Depends

from faststream.broker.core.asyncronous import default_filter
from faststream.broker.middlewares import BaseMiddleware
from faststream.broker.types import (
    AsyncCustomDecoder,
    AsyncCustomParser,
    Filter,
    T_HandlerReturn,
)
from faststream.rabbit.message import RabbitMessage
from faststream.rabbit.shared.schemas import RabbitExchange, RabbitQueue
from faststream.types import AnyDict

class RabbitRoute:
    """Delayed `RabbitBroker.subscriber()` registration object"""

    def __init__(
        self,
        call: Callable[..., T_HandlerReturn],
        queue: Union[str, RabbitQueue],
        exchange: Union[str, RabbitExchange, None] = None,
        *,
        consume_args: Optional[AnyDict] = None,
        # broker arguments
        dependencies: Sequence[Depends] = (),
        filter: Filter[RabbitMessage] = default_filter,
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
    ) -> None: ...
