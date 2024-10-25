from faststream.rabbit.utils import is_routing_exchange
from faststream.specification.asyncapi.utils import resolve_payloads
from faststream.specification.schema.bindings import (
    ChannelBinding,
    OperationBinding,
    amqp,
)
from faststream.specification.schema.channel import Channel
from faststream.specification.schema.message import CorrelationId, Message
from faststream.specification.schema.operation import Operation

from .usecase import LogicPublisher


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

    def get_name(self) -> str:
        routing = (
            self.routing_key
            or (self.queue.routing if is_routing_exchange(self.exchange) else None)
            or "_"
        )

        return f"{routing}:{getattr(self.exchange, 'name', None) or '_'}:Publisher"

    def get_schema(self) -> dict[str, Channel]:
        payloads = self.get_payloads()

        return {
            self.name: Channel(
                description=self.description,
                publish=Operation(
                    bindings=OperationBinding(
                        amqp=amqp.OperationBinding(
                            cc=self.routing or None,
                            deliveryMode=2 if self.message_options.get("persist") else 1,
                            replyTo=self.message_options.get("reply_to"),  # type: ignore[arg-type]
                            mandatory=self.publish_options.get("mandatory"),  # type: ignore[arg-type]
                            priority=self.message_options.get("priority"),  # type: ignore[arg-type]
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
                            location="$message.header#/correlation_id",
                        ),
                    ),
                ),
                bindings=ChannelBinding(
                    amqp=amqp.ChannelBinding(
                        is_="routingKey",
                        queue=amqp.Queue(
                            name=self.queue.name,
                            durable=self.queue.durable,
                            exclusive=self.queue.exclusive,
                            autoDelete=self.queue.auto_delete,
                            vhost=self.virtual_host,
                        )
                        if is_routing_exchange(self.exchange) and self.queue.name
                        else None,
                        exchange=(
                            amqp.Exchange(type="default", vhost=self.virtual_host)
                            if not self.exchange.name
                            else amqp.Exchange(
                                type=self.exchange.type.value,
                                name=self.exchange.name,
                                durable=self.exchange.durable,
                                autoDelete=self.exchange.auto_delete,
                                vhost=self.virtual_host,
                            )
                        ),
                    ),
                ),
            ),
        }
