from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from faststream._internal.types import BrokerMiddleware, MsgType


@dataclass
class SpecificationConfigs:
    title_: Optional[str]
    description_: Optional[str]
    include_in_schema: bool


@dataclass
class UseCaseOptions:
    broker_middlewares: Sequence["BrokerMiddleware[MsgType]"]
