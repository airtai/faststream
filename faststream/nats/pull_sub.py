from typing import Any, List, Optional

from nats.js.api import (
    DiscardPolicy,
    ExternalStream,
    Placement,
    RePublish,
    RetentionPolicy,
    StorageType,
    StreamConfig,
    StreamSource,
)
from pydantic import Field, BaseModel


__all__ = (
    "PullSub",
    # import to prevent Pydantic ForwardRef error
    "RetentionPolicy",
    "DiscardPolicy",
    "StorageType",
    "Placement",
    "StreamSource",
    "ExternalStream",
    "RePublish",
    "Optional",
)


class PullSub(BaseModel):
    config: StreamConfig

    subjects: List[str] = Field(default_factory=list)
    declare: bool = Field(default=True)

    # idk which parameters must be here....

    def __init__(
        self,
        batch_size: int,
        *args: Any,
        declare: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            declare=declare,
            subjects=[],
            batch_size=batch_size,
            config=StreamConfig(
                *args,
                **kwargs,  # type: ignore[misc]
            ),
        )
