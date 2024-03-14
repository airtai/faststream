from dataclasses import dataclass
from typing import Optional

from typing_extensions import Annotated, Doc


@dataclass(slots=True)
class PullSub:
    """A class to represent a NATS pull subscription."""

    batch_size: Annotated[int, Doc("Consuming messages batch size."),] = 1
    timeout: Annotated[Optional[float], Doc("Wait this time for required batch size will be accumulated in stream."),] = 5.0
    batch: Annotated[bool, Doc("Whether to propogate consuming batch as iterable object to your handler."),] = False
