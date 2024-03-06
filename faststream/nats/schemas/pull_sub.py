from typing import Optional
from dataclasses import dataclass


@dataclass(slots=True)
class PullSub:
    """A class to represent a NATS pull subscription."""

    batch_size: int = 1
    timeout: Optional[float] = 5.0
    batch: bool = False
