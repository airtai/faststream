from dataclasses import dataclass
from typing import (
    Optional,
    Union,
)

from faststream._internal.publisher.schemas import PublisherUsecaseOptions


@dataclass
class PublisherDefaultOptions:
    key: Union[bytes, str, None]
    topic: str
    partition: Optional[int]
    headers: Optional[dict[str, str]]
    reply_to: Optional[str]


@dataclass
class KafkaPublisherBaseOptions(PublisherDefaultOptions):
    internal_options: PublisherUsecaseOptions
