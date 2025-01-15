from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from faststream._internal.subscriber.schemas import InternalOptions

if TYPE_CHECKING:
    from faststream._internal.basic_types import AnyDict
    from faststream.rabbit.schemas.exchange import RabbitExchange
    from faststream.rabbit.schemas.queue import RabbitQueue


@dataclass
class LogicOptions:
    queue: "RabbitQueue"
    consume_args: Optional["AnyDict"]
    internal_options: InternalOptions


@dataclass
class SpecificationOptions:
    queue: "RabbitQueue"
    title_: Optional[str]
    description_: Optional[str]
    include_in_schema: bool
    exchange: "RabbitExchange"
