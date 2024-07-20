from typing import TYPE_CHECKING, Iterable, Optional

from faststream.broker.response import Response

if TYPE_CHECKING:
    from aio_pika.abc import DateType
    from typing_extensions import Unpack

    from faststream.broker.types import PublisherMiddleware
    from faststream.rabbit import RabbitExchange, RabbitQueue
    from faststream.rabbit.publisher.usecase import PublishKwargs
    from faststream.rabbit.types import AioPikaSendableMessage


class RabbitResponse(Response):
    def __init__(
        self,
        message: "AioPikaSendableMessage",
        queue: Optional["RabbitQueue"] = None,
        exchange: Optional["RabbitExchange"] = None,
        *,
        routing_key: str = "",
        correlation_id: Optional[str] = None,
        message_id: Optional[str] = None,
        timestamp: Optional["DateType"] = None,
        rpc: bool = False,
        rpc_timeout: Optional[float] = 30.0,
        raise_timeout: bool = False,
        _extra_middlewares: Iterable["PublisherMiddleware"] = (),
        **publish_kwargs: "Unpack[PublishKwargs]",
    ) -> None: ...
