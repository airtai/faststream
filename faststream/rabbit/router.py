from typing import Any, Dict, Optional, Union

from faststream._compat import model_copy, override
from faststream.rabbit.asyncapi import Publisher
from faststream.rabbit.shared.router import RabbitRouter as BaseRouter
from faststream.rabbit.shared.schemas import (
    RabbitExchange,
    RabbitQueue,
    get_routing_hash,
)
from faststream.rabbit.shared.types import TimeoutType


class RabbitRouter(BaseRouter):
    _publishers: Dict[int, Publisher]

    @staticmethod
    def _get_publisher_key(publisher: Publisher) -> int:
        return get_routing_hash(publisher.queue, publisher.exchange)

    @staticmethod
    def _update_publisher_prefix(prefix: str, publisher: Publisher) -> Publisher:
        publisher.queue = model_copy(
            publisher.queue, update={"name": prefix + publisher.queue.name}
        )
        return publisher

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
                message_kwargs=message_kwargs,
                title=title,
                _description=description,
            ),
        )
        key = self._get_publisher_key(new_publisher)
        publisher = self._publishers[key] = self._publishers.get(key, new_publisher)
        return publisher
