from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, Optional, Union

from aio_pika.message import IncomingMessage
from typing_extensions import override

from faststream._compat import model_copy
from faststream.broker.router import BrokerRoute as RabbitRoute
from faststream.broker.router import BrokerRouter
from faststream.broker.types import P_HandlerParams, T_HandlerReturn
from faststream.rabbit.asyncapi import Publisher
from faststream.rabbit.schemas.schemas import (
    RabbitExchange,
    RabbitQueue,
)

if TYPE_CHECKING:
    from faststream.broker.core.call_wrapper import HandlerCallWrapper
    from faststream.broker.types import PublisherMiddleware
    from faststream.rabbit.types import TimeoutType
    from faststream.types import SendableMessage


class RabbitRouter(BrokerRouter[int, "IncomingMessage"]):
    _publishers: Dict[int, Publisher]

    def __init__(
        self,
        prefix: str = "",
        handlers: Iterable[RabbitRoute["IncomingMessage", "SendableMessage"]] = (),
        **kwargs: Any,
    ) -> None:
        for h in handlers:
            if (q := h.kwargs.pop("queue", None)) is None:
                q, h.args = h.args[0], h.args[1:]
            queue = RabbitQueue.validate(q)
            new_q = model_copy(queue, update={"name": prefix + queue.name})
            h.args = (new_q, *h.args)

        super().__init__(prefix, handlers, **kwargs)

    @override
    def subscriber(  # type: ignore[override]
        self,
        queue: Union[str, RabbitQueue],
        *broker_args: Any,
        **broker_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        "HandlerCallWrapper[IncomingMessage, P_HandlerParams, T_HandlerReturn]",
    ]:
        q = RabbitQueue.validate(queue)
        new_q = model_copy(q, update={"name": self.prefix + q.name})
        return self._wrap_subscriber(new_q, *broker_args, **broker_kwargs)

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
        middlewares: Iterable["PublisherMiddleware"] = (),
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        schema: Optional[Any] = None,
        include_in_schema: bool = True,
        priority: Optional[int] = None,
        **message_kwargs: Any,
    ) -> Publisher:
        new_publisher = self._update_publisher_prefix(
            self.prefix,
            Publisher(
                queue=RabbitQueue.validate(queue),
                exchange=RabbitExchange.validate(exchange),
                routing_key=routing_key,
                mandatory=mandatory,
                immediate=immediate,
                timeout=timeout,
                persist=persist,
                reply_to=reply_to,
                priority=priority,
                message_kwargs=message_kwargs,
                middlewares=middlewares,
                # AsyncAPI
                title_=title,
                description_=description,
                schema_=schema,
                include_in_schema=(
                    include_in_schema
                    if self.include_in_schema is None
                    else self.include_in_schema
                ),
            ),
        )
        key = self._get_publisher_key(new_publisher)
        publisher = self._publishers[key] = self._publishers.get(key, new_publisher)
        return publisher

    @staticmethod
    def _get_publisher_key(publisher: Publisher) -> int:
        return publisher._get_routing_hash()

    @staticmethod
    def _update_publisher_prefix(prefix: str, publisher: Publisher) -> Publisher:
        publisher.queue = model_copy(
            publisher.queue, update={"name": prefix + publisher.queue.name}
        )
        return publisher
