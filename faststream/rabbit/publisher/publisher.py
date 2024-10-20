from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Optional

from typing_extensions import override

from faststream.rabbit.publisher.usecase import LogicPublisher, PublishKwargs
from faststream.rabbit.utils import is_routing_exchange
from faststream.specification.asyncapi.utils import resolve_payloads
from faststream.specification.schema import Message, Operation, PublisherSpec
from faststream.specification.schema.bindings import (
    ChannelBinding,
    OperationBinding,
    amqp,
)

if TYPE_CHECKING:
    from aio_pika import IncomingMessage

    from faststream._internal.types import BrokerMiddleware, PublisherMiddleware
    from faststream.rabbit.schemas import RabbitExchange, RabbitQueue


class SpecificationPublisher(LogicPublisher):
    """AsyncAPI-compatible Rabbit Publisher class.

    Creating by

    ```python
           publisher: SpecificationPublisher = (
               broker.publisher(...)
           )
           # or
           publisher: SpecificationPublisher = (
               router.publisher(...)
           )
    ```
    """

    def get_default_name(self) -> str:
        routing = (
            self.routing_key
            or (self.queue.routing if is_routing_exchange(self.exchange) else None)
            or "_"
        )

        return f"{routing}:{getattr(self.exchange, 'name', None) or '_'}:Publisher"

    def get_schema(self) -> dict[str, PublisherSpec]:
        payloads = self.get_payloads()

        return {
            self.name: PublisherSpec(
                description=self.description,
                operation=Operation(
                    bindings=OperationBinding(
                        amqp=amqp.OperationBinding(
                            routing_key=self.routing or None,
                            queue=amqp.Queue.from_queue(self.queue),
                            exchange=amqp.Exchange.from_exchange(self.exchange),
                            ack=True,
                            persist=self.message_kwargs.get("persist"),
                            mandatory=self.message_kwargs.get("mandatory"),  # type: ignore[arg-type]
                            reply_to=self.message_kwargs.get("reply_to"),  # type: ignore[arg-type]
                            priority=self.message_kwargs.get("priority"),  # type: ignore[arg-type]
                        ),
                    ),
                    message=Message(
                        title=f"{self.name}:Message",
                        payload=resolve_payloads(
                            payloads,
                            "Publisher",
                            served_words=2 if self.title_ is None else 1,
                        ),
                    ),
                ),
                bindings=ChannelBinding(
                    amqp=amqp.ChannelBinding(
                        virtual_host=self.virtual_host,
                        queue=amqp.Queue.from_queue(self.queue),
                        exchange=amqp.Exchange.from_exchange(self.exchange),
                    ),
                ),
            ),
        }

    @override
    @classmethod
    def create(  # type: ignore[override]
        cls,
        *,
        routing_key: str,
        queue: "RabbitQueue",
        exchange: "RabbitExchange",
        message_kwargs: "PublishKwargs",
        # Publisher args
        broker_middlewares: Iterable["BrokerMiddleware[IncomingMessage]"],
        middlewares: Iterable["PublisherMiddleware"],
        # AsyncAPI args
        schema_: Optional[Any],
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> "SpecificationPublisher":
        return cls(
            routing_key=routing_key,
            queue=queue,
            exchange=exchange,
            message_kwargs=message_kwargs,
            # Publisher args
            broker_middlewares=broker_middlewares,
            middlewares=middlewares,
            # AsyncAPI args
            schema_=schema_,
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )
