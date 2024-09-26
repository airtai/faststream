"""AsyncAPI AMQP bindings.

References: https://github.com/asyncapi/bindings/tree/master/amqp
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field
from typing_extensions import Self

from faststream.specification import schema as spec


class Queue(BaseModel):
    """A class to represent a queue.

    Attributes:
        name : name of the queue
        durable : indicates if the queue is durable
        exclusive : indicates if the queue is exclusive
        autoDelete : indicates if the queue should be automatically deleted
        vhost : virtual host of the queue (default is "/")
    """

    name: str
    durable: bool
    exclusive: bool
    autoDelete: bool
    vhost: str = "/"

    @classmethod
    def from_spec(cls, binding: spec.bindings.amqp.Queue) -> Self:
        return cls(
            name=binding.name,
            durable=binding.durable,
            exclusive=binding.exclusive,
            autoDelete=binding.autoDelete,
            vhost=binding.vhost,
        )


class Exchange(BaseModel):
    """A class to represent an exchange.

    Attributes:
        name : name of the exchange (optional)
        type : type of the exchange, can be one of "default", "direct", "topic", "fanout", "headers"
        durable : whether the exchange is durable (optional)
        autoDelete : whether the exchange is automatically deleted (optional)
        vhost : virtual host of the exchange, default is "/"
    """

    name: Optional[str] = None
    type: Literal[
        "default",
        "direct",
        "topic",
        "fanout",
        "headers",
        "x-delayed-message",
        "x-consistent-hash",
        "x-modulus-hash",
    ]
    durable: Optional[bool] = None
    autoDelete: Optional[bool] = None
    vhost: str = "/"

    @classmethod
    def from_spec(cls, binding: spec.bindings.amqp.Exchange) -> Self:
        return cls(
            name=binding.name,
            type=binding.type,
            durable=binding.durable,
            autoDelete=binding.autoDelete,
            vhost=binding.vhost,
        )


class ChannelBinding(BaseModel):
    """A class to represent channel binding.

    Attributes:
        is_ : Type of binding, can be "queue" or "routingKey"
        bindingVersion : Version of the binding
        queue : Optional queue object
        exchange : Optional exchange object
    """

    is_: Literal["queue", "routingKey"] = Field(..., alias="is")
    bindingVersion: str = "0.2.0"
    queue: Optional[Queue] = None
    exchange: Optional[Exchange] = None

    @classmethod
    def from_spec(cls, binding: spec.bindings.amqp.ChannelBinding) -> Self:
        return cls(
            **{
                "is": "routingKey",

                "queue": Queue.from_spec(binding.queue)
                if binding.queue is not None
                   and binding.queue.name
                   and binding.exchange
                   and binding.exchange.type in ("default", "direct", "topic")
                else None,

                "exchange": Exchange.from_spec(binding.exchange)
                if binding.exchange is not None
                else None,
            },
        )


def from_spec(binding: spec.bindings.amqp.ChannelBinding) -> ChannelBinding:
    return ChannelBinding.from_spec(binding)
