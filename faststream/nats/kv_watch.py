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
from pydantic import BaseModel, Field

__all__ = (
    "KvWatch",
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


class KvWatch(BaseModel):
    config: StreamConfig

    subjects: List[str] = Field(default_factory=list)
    declare: bool = Field(default=True)

    def __init__(
        self,
        bucket: str,
        keys,
        headers_only: bool = False,
        include_history: bool = False,
        ignore_deletes: bool = False,
        meta_only: bool = False,
        *args: Any,
        declare: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            declare=declare,
            subjects=[],
            keys=keys,
            bucket=bucket,
            headers_only=headers_only,
            include_history=include_history,
            ignore_deletes=ignore_deletes,
            meta_only=meta_only,
            config=StreamConfig(
                *args,
                **kwargs,  # type: ignore[misc]
            ),
        )
