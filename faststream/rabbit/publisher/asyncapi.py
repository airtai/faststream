from typing import TYPE_CHECKING, Any, Dict, Iterable, Optional

from typing_extensions import override

from faststream.asyncapi.schema import (
    Channel,
    ChannelBinding,
    CorrelationId,
    Message,
    Operation,
    OperationBinding,
)
from faststream.asyncapi.schema.bindings import amqp
from faststream.asyncapi.utils import resolve_payloads
from faststream.rabbit.publisher.usecase import LogicPublisher, PublishKwargs
from faststream.rabbit.utils import is_routing_exchange

if TYPE_CHECKING:
    from aio_pika import IncomingMessage

    from faststream.broker.types import BrokerMiddleware, PublisherMiddleware
    from faststream.rabbit.schemas import RabbitExchange, RabbitQueue


class AsyncAPIPublisher(LogicPublisher):
    """AsyncAPI-compatible Rabbit Publisher class.

    Creting by

    ```python
    publisher: AsyncAPIPublisher = broker.publisher(...)
    # or
    publisher: AsyncAPIPublisher = router.publisher(...)
    ```

    """

    def get_name(self) -> str:
        routing = (
            self.routing_key
            or (self.queue.routing if is_routing_exchange(self.exchange) else None)
            or "_"
        )
        return f"{routing}:{getattr(self.exchange, 'name', '_')}:Publisher"

    def get_schema(self) -> Dict[str, Channel]:
        payloads = self.get_payloads()

        return {
            self.name: Channel(
                description=self.description,  # type: ignore[attr-defined]
                publish=Operation(
                    bindings=OperationBinding(
                        amqp=amqp.OperationBinding(
                            cc=self.routing or None,
                            deliveryMode=2 if self.message_kwargs.get("persist") else 1,
                            mandatory=self.message_kwargs.get("mandatory"),
                            replyTo=self.message_kwargs.get("reply_to"),
                            priority=self.message_kwargs.get("priority"),
                        ),
                    )
                    if is_routing_exchange(self.exchange)
                    else None,
                    message=Message(
                        title=f"{self.name}:Message",
                        payload=resolve_payloads(
                            payloads,
                            "Publisher",
                            served_words=2 if self.title_ is None else 1,
                        ),
                        correlationId=CorrelationId(
                            location="$message.header#/correlation_id"
                        ),
                    ),
                ),
                bindings=ChannelBinding(
                    amqp=amqp.ChannelBinding(
                        **{
                            "is": "routingKey",  # type: ignore
                            "queue": amqp.Queue(
                                name=self.queue.name,
                                durable=self.queue.durable,
                                exclusive=self.queue.exclusive,
                                autoDelete=self.queue.auto_delete,
                                vhost=self.virtual_host,
                            )
                            if is_routing_exchange(self.exchange) and self.queue.name
                            else None,
                            "exchange": (
                                amqp.Exchange(type="default", vhost=self.virtual_host)
                                if self.exchange is None
                                else amqp.Exchange(
                                    type=self.exchange.type.value,  # type: ignore
                                    name=self.exchange.name,
                                    durable=self.exchange.durable,
                                    autoDelete=self.exchange.auto_delete,
                                    vhost=self.virtual_host,
                                )
                            ),
                        }
                    )
                ),
            )
        }

    @override
    @classmethod
    def create(  # type: ignore[override]
        cls,
        *,
        routing_key: str,
        queue: "RabbitQueue",
        exchange: Optional["RabbitExchange"],
        message_kwargs: "PublishKwargs",
        # Publisher args
        broker_middlewares: Iterable["BrokerMiddleware[IncomingMessage]"],
        middlewares: Iterable["PublisherMiddleware"],
        # AsyncAPI args
        schema_: Optional[Any],
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> "AsyncAPIPublisher":
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
