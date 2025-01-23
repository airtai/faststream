from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from faststream._internal.constants import EMPTY
from faststream.middlewares import AckPolicy
from faststream.specification.schema import (
    SpecificationOptions as SpecificationSubscriberOptions,  # noqa: F401.
    UseCaseOptions,
)

if TYPE_CHECKING:
    from fast_depends.dependencies import Dependant

    from faststream._internal.types import (
        AsyncCallable,
    )


@dataclass
class SubscriberUsecaseOptions(UseCaseOptions):
    no_reply: bool
    broker_dependencies: Iterable["Dependant"]
    ack_policy: AckPolicy
    default_parser: Optional["AsyncCallable"] = field(default_factory=EMPTY)
    default_decoder: Optional["AsyncCallable"] = field(default_factory=EMPTY)
