from typing import Any, Dict, Optional, Union

from propan._compat import model_copy, override
from propan.rabbit.asyncapi import Publisher
from propan.rabbit.shared.router import RabbitRouter as BaseRouter
from propan.rabbit.shared.schemas import RabbitExchange, RabbitQueue, get_routing_hash
from propan.rabbit.shared.types import TimeoutType


class RabbitRouter(BaseRouter):
    _publishers: Dict[int, Publisher]  # type: ignore[assignment]

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
        **message_kwargs: Any,
    ) -> Publisher:
        q = RabbitQueue.validate(queue)
        q_copy = model_copy(q, update={"name": self.prefix + q.name})
        ex = RabbitExchange.validate(exchange)
        key = get_routing_hash(q_copy, ex)
        publisher = self._publishers[key] = self._publishers.get(
            key,
            Publisher(
                queue=q_copy,
                exchange=ex,
                routing_key=routing_key,
                mandatory=mandatory,
                immediate=immediate,
                timeout=timeout,
                persist=persist,
                reply_to=reply_to,
                message_kwargs=message_kwargs,
                title=title,
                _description=description,
            ),
        )
        return publisher
