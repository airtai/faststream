from typing import Dict

from faststream.specification.asyncapi.v2_6_0 import schema as v2_6_0
from faststream.rabbit.subscriber.usecase import LogicSubscriber
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


class SpecificationSubscriber(LogicSubscriber):
    """AsyncAPI-compatible Rabbit Subscriber class."""

    def get_name(self) -> str:
        return f"{self.queue.name}:{getattr(self.exchange, 'name', None) or '_'}:{self.call_name}"

    def get_schema(self) -> Dict[str, Channel]:
        payloads = self.get_payloads()

        return {
            self.name: Channel(
                description=self.description,  # type: ignore[attr-defined]
                subscribe=Operation(
                    bindings=OperationBinding(
                        amqp=amqp.OperationBinding(
                            cc=self.queue.routing,
                        ),
                    )
                    if is_routing_exchange(self.exchange)
                    else None,
                    message=Message(
                        title=f"{self.name}:Message",
                        payload=resolve_payloads(payloads),
                        correlationId=CorrelationId(
                            location="$message.header#/correlation_id"
                        ),
                    ),
                ),
                bindings=ChannelBinding(
                    amqp=amqp.ChannelBinding(
                        **{
                            "is_": "routingKey",  # type: ignore
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
                                if not self.exchange.name
                                else amqp.Exchange(
                                    type=self.exchange.type.value,
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
