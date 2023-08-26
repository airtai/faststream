from typing import Any, Awaitable, Callable, Optional, Sequence, Union

import aio_pika
from fast_depends.dependencies import Depends

from propan.broker.core.asyncronous import default_filter
from propan.broker.message import PropanMessage
from propan.broker.middlewares import BaseMiddleware
from propan.broker.types import AsyncCustomDecoder, AsyncCustomParser, T_HandlerReturn
from propan.rabbit.shared.schemas import RabbitExchange, RabbitQueue
from propan.types import AnyDict

RabbitMessage = PropanMessage[aio_pika.IncomingMessage]

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
    ) -> None: ...
