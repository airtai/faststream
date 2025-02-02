from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from faststream._internal.publisher.configs import PublisherUsecaseOptions

if TYPE_CHECKING:
    from faststream._internal.basic_types import AnyDict


@dataclass
class RedisPublisherBaseOptions:
    reply_to: str
    headers: Optional["AnyDict"]
    internal_options: PublisherUsecaseOptions
