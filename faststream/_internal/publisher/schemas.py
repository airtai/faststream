from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

from faststream.specification.schema import SpecificationOptions, UseCaseOptions

if TYPE_CHECKING:
    from faststream._internal.types import (
        PublisherMiddleware,
    )


@dataclass
class SpecificationPublisherOptions(SpecificationOptions):
    schema_: Optional[Any]


@dataclass
class PublisherUsecaseOptions(UseCaseOptions):
    middlewares: Sequence["PublisherMiddleware"]
