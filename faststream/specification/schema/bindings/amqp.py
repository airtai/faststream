"""AsyncAPI AMQP bindings.

References: https://github.com/asyncapi/bindings/tree/master/amqp
"""
from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class Queue:
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


@dataclass
class Exchange:
    """A class to represent an exchange.

    Attributes:
        name : name of the exchange (optional)
        type : type of the exchange, can be one of "default", "direct", "topic", "fanout", "headers"
        durable : whether the exchange is durable (optional)
        autoDelete : whether the exchange is automatically deleted (optional)
        vhost : virtual host of the exchange, default is "/"
    """

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

    name: Optional[str] = None
    durable: Optional[bool] = None
    autoDelete: Optional[bool] = None
    vhost: str = "/"


@dataclass
class ChannelBinding:
    """A class to represent channel binding.

    Attributes:
        is_ : Type of binding, can be "queue" or "routingKey"
        bindingVersion : Version of the binding
        queue : Optional queue object
        exchange : Optional exchange object
    """

    is_: Literal["queue", "routingKey"]
    bindingVersion: str = "0.2.0"
    queue: Optional[Queue] = None
    exchange: Optional[Exchange] = None


@dataclass
class OperationBinding:
    """A class to represent an operation binding.

    Attributes:
        cc : optional string representing the cc
        ack : boolean indicating if the operation is acknowledged
        replyTo : optional dictionary representing the replyTo
        bindingVersion : string representing the binding version
    """

    cc: Optional[str] = None
    ack: bool = True
    replyTo: Optional[str] = None
    deliveryMode: Optional[int] = None
    mandatory: Optional[bool] = None
    priority: Optional[int] = None
    bindingVersion: str = "0.2.0"
