from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

from faststream.specification.schema.base import SpecificationOptions

if TYPE_CHECKING:
    from faststream._internal.types import (
        BrokerMiddleware,
        MsgType,
        PublisherMiddleware,
    )


@dataclass
class SpecificationPublisherOptions(SpecificationOptions):
    schema_: Optional[Any]


@dataclass
class PublisherUsecaseOptions:
    broker_middlewares: Sequence["BrokerMiddleware[MsgType]"]
    middlewares: Sequence["PublisherMiddleware"]
