from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from faststream._internal.subscriber.configs import SubscriberUseCaseConfigs

if TYPE_CHECKING:
    from faststream._internal.basic_types import AnyDict
    from faststream.rabbit.schemas.queue import RabbitQueue


@dataclass
class RabbitSubscriberBaseConfigs(SubscriberUseCaseConfigs):
    queue: "RabbitQueue"
    consume_args: Optional["AnyDict"]
