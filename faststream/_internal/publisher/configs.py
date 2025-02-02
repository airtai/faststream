from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

from faststream._internal.configs import SpecificationConfigs, UseCaseOptions

if TYPE_CHECKING:
    from faststream._internal.types import (
        PublisherMiddleware,
    )


@dataclass
class SpecificationPublisherOptions(SpecificationConfigs):
    schema_: Optional[Any]


@dataclass
class PublisherUsecaseOptions(UseCaseOptions):
    middlewares: Sequence["PublisherMiddleware"]
