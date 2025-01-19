from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Optional,
)

from faststream._internal.subscriber.schemas import SubscriberUsecaseOptions

if TYPE_CHECKING:
    from nats.js.api import ConsumerConfig

    from faststream._internal.basic_types import (
        AnyDict,
    )


@dataclass
class DefaultNatsSubscriberOptions:
    subject: str
    config: "ConsumerConfig"
    extra_options: Optional["AnyDict"]  # вот тут возможно добавить EMPTY


@dataclass
class NatsLogicSubscriberOptions(DefaultNatsSubscriberOptions):
    internal_options: SubscriberUsecaseOptions
