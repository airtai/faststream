from dataclasses import dataclass
from typing import Optional

from .bindings import ChannelBinding
from .operation import Operation


@dataclass
class SubscriberSpec:
    description: str
    operation: Operation
    bindings: Optional[ChannelBinding]
