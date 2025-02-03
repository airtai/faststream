from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Optional,
)

from faststream._internal.subscriber.configs import SubscriberUseCaseConfigs
from faststream.exceptions import SetupError

if TYPE_CHECKING:
    from nats.js.api import ConsumerConfig

    from faststream._internal.basic_types import (
        AnyDict,
    )


@dataclass
class NatsSubscriberBaseConfigs(SubscriberUseCaseConfigs):
    subject: str
    config: "ConsumerConfig"
    extra_options: Optional["AnyDict"]

    def __post_init__(self) -> None:
        if not self.subject and not self.config:
            msg = "You must provide either the `subject` or `config` option."
            raise SetupError(msg)
