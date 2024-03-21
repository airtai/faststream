from typing import Dict, Optional

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
from faststream.rabbit.handler import LogicHandler
from faststream.rabbit.publisher import LogicPublisher
from faststream.rabbit.schemas.constants import ExchangeType
from faststream.rabbit.schemas.schemas import RabbitExchange


class Publisher(LogicPublisher):
    """AsyncAPI-compatible Rabbit Publisher class"""

    def get_name(self) -> str:
        routing = (
            self.routing_key
            or (self.queue.routing if _is_routing_exchange(self.exchange) else None)
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
                    if _is_routing_exchange(self.exchange)
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
                            if _is_routing_exchange(self.exchange)
                            else None,
                            "exchange": (
                                amqp.Exchange(type="default", vhost=self.virtual_host)
                                if self.exchange is None
                                else amqp.Exchange(
                                    type=self.exchange.type,  # type: ignore
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


class Handler(LogicHandler):
    """AsyncAPI-compatible Rabbit Handler class"""

    def get_name(self) -> str:
        return (
            f"{self.queue.name}:{getattr(self.exchange, 'name', '_')}:{self.call_name}"
        )

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
                    if _is_routing_exchange(self.exchange)
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
                            "is": "routingKey",  # type: ignore
                            "queue": amqp.Queue(
                                name=self.queue.name,
                                durable=self.queue.durable,
                                exclusive=self.queue.exclusive,
                                autoDelete=self.queue.auto_delete,
                                vhost=self.virtual_host,
                            )
                            if _is_routing_exchange(self.exchange)
                            else None,
                            "exchange": (
                                amqp.Exchange(type="default", vhost=self.virtual_host)
                                if self.exchange is None
                                else amqp.Exchange(
                                    type=self.exchange.type,  # type: ignore
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


def _is_routing_exchange(exchange: Optional[RabbitExchange]) -> bool:
    """Check if an exchange requires routing_key to deliver message."""
    return not exchange or exchange.type in (
        ExchangeType.DIRECT.value,
        ExchangeType.TOPIC.value,
    )
