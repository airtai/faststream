from collections.abc import Iterable
from typing import TYPE_CHECKING, Optional

from faststream._internal.constants import EMPTY
from faststream.middlewares import AckPolicy
from faststream.rabbit.subscriber.specified import SpecificationSubscriber

if TYPE_CHECKING:
    from aio_pika import IncomingMessage
    from fast_depends.dependencies import Dependant

    from faststream._internal.basic_types import AnyDict
    from faststream._internal.types import BrokerMiddleware
    from faststream.rabbit.schemas import RabbitExchange, RabbitQueue


def create_subscriber(
    *,
    queue: "RabbitQueue",
    exchange: "RabbitExchange",
    consume_args: Optional["AnyDict"],
    # Subscriber args
    no_reply: bool,
    broker_dependencies: Iterable["Dependant"],
    broker_middlewares: Iterable["BrokerMiddleware[IncomingMessage]"],
    ack_policy: "AckPolicy" = EMPTY,
    # AsyncAPI args
    title_: Optional[str],
    description_: Optional[str],
    include_in_schema: bool,
) -> SpecificationSubscriber:
    return SpecificationSubscriber(
        queue=queue,
        exchange=exchange,
        consume_args=consume_args,
        ack_policy=AckPolicy.REJECT_ON_ERROR if ack_policy is EMPTY else ack_policy,
        no_reply=no_reply,
        broker_dependencies=broker_dependencies,
        broker_middlewares=broker_middlewares,
        title_=title_,
        description_=description_,
        include_in_schema=include_in_schema,
    )
