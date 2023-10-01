from typing import List, Optional

from nats.js.api import (
    DiscardPolicy,
    Placement,
    RePublish,
    RetentionPolicy,
    StorageType,
    StreamConfig,
    StreamSource,
)
from pydantic import Field

from faststream.broker.schemas import NameRequired

class JStream(NameRequired):
    config: StreamConfig

    subjects: List[str] = Field(default_factory=list)
    declare: bool = Field(default=True)

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        subjects: Optional[List[str]] = None,
        retention: Optional[RetentionPolicy] = None,
        max_consumers: Optional[int] = None,
        max_msgs: Optional[int] = None,
        max_bytes: Optional[int] = None,
        discard: Optional[DiscardPolicy] = DiscardPolicy.OLD,
        max_age: Optional[float] = None,  # in seconds
        max_msgs_per_subject: int = -1,
        max_msg_size: Optional[int] = -1,
        storage: Optional[StorageType] = None,
        num_replicas: Optional[int] = None,
        no_ack: bool = False,
        template_owner: Optional[str] = None,
        duplicate_window: float = 0,
        placement: Optional[Placement] = None,
        mirror: Optional[StreamSource] = None,
        sources: Optional[List[StreamSource]] = None,
        sealed: bool = False,
        deny_delete: bool = False,
        deny_purge: bool = False,
        allow_rollup_hdrs: bool = False,
        republish: Optional[RePublish] = None,
        allow_direct: Optional[bool] = None,
        mirror_direct: Optional[bool] = None,
        # custom
        declare: bool = True,
    ) -> None: ...
