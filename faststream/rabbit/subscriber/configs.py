from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from faststream._internal.subscriber.configs import SubscriberUsecaseOptions

if TYPE_CHECKING:
    from faststream._internal.basic_types import AnyDict
    from faststream.rabbit.schemas.queue import RabbitQueue


@dataclass
class RabbitSubscriberBaseOptions:
    internal_options: SubscriberUsecaseOptions
    queue: "RabbitQueue"
    consume_args: Optional["AnyDict"]
