from typing import TYPE_CHECKING, Dict, Iterable, Optional, Union

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
from faststream.rabbit.schemas import RabbitExchange, RabbitQueue, ReplyConfig
from faststream.rabbit.subscriber.usecase import LogicSubscriber
from faststream.rabbit.utils import is_routing_exchange

if TYPE_CHECKING:
    from aio_pika import IncomingMessage
    from fast_depends.dependencies import Depends

    from faststream.broker.types import BrokerMiddleware
    from faststream.types import AnyDict


class AsyncAPISubscriber(LogicSubscriber):
    """AsyncAPI-compatible Rabbit Subscriber class."""

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
        queue: RabbitQueue,
        exchange: Optional["RabbitExchange"],
        consume_args: Optional["AnyDict"],
        reply_config: Optional["ReplyConfig"],
        # Subscriber args
        no_ack: bool,
        retry: Union[bool, int],
        broker_dependencies: Iterable["Depends"],
        broker_middlewares: Iterable["BrokerMiddleware[IncomingMessage]"],
        # AsyncAPI args
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> "AsyncAPISubscriber":
        return cls(
            queue=queue,
            exchange=exchange,
            consume_args=consume_args,
            reply_config=reply_config,
            no_ack=no_ack,
            retry=retry,
            broker_dependencies=broker_dependencies,
            broker_middlewares=broker_middlewares,
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )
