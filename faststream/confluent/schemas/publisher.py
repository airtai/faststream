from dataclasses import dataclass
from typing import (
    Optional,
    Union,
)

from faststream._internal.publisher.schemas import PublisherUsecaseOptions


@dataclass
class ConfluentPublisherBaseOptions:
    key: Union[bytes, str, None]
    topic: str
    partition: Optional[int]
    headers: Optional[dict[str, str]]
    reply_to: Optional[str]
    internal_options: PublisherUsecaseOptions
