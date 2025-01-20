from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from faststream._internal.publisher.schemas import (
    PublisherUsecaseOptions,
)

if TYPE_CHECKING:
    from faststream.nats.schemas import JStream


@dataclass
class NatsPublisherBaseOptions:
    subject: str
    reply_to: str
    headers: Optional[dict[str, str]]
    stream: Optional["JStream"]
    timeout: Optional[float]
    internal_options: PublisherUsecaseOptions
