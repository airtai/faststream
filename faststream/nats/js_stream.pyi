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

    subjects: list[str] = Field(default_factory=list)
    declare: bool = Field(default=True)

    def __init__(
        self,
        name: str,
        description: str | None = None,
        subjects: list[str] | None = None,
        retention: RetentionPolicy | None = None,
        max_consumers: int | None = None,
        max_msgs: int | None = None,
        max_bytes: int | None = None,
        discard: DiscardPolicy | None = DiscardPolicy.OLD,
        max_age: float | None = None,  # in seconds
        max_msgs_per_subject: int = -1,
        max_msg_size: int | None = -1,
        storage: StorageType | None = None,
        num_replicas: int | None = None,
        no_ack: bool = False,
        template_owner: str | None = None,
        duplicate_window: float = 0,
        placement: Placement | None = None,
        mirror: StreamSource | None = None,
        sources: list[StreamSource] | None = None,
        sealed: bool = False,
        deny_delete: bool = False,
        deny_purge: bool = False,
        allow_rollup_hdrs: bool = False,
        republish: RePublish | None = None,
        allow_direct: bool | None = None,
        mirror_direct: bool | None = None,
        # custom
        declare: bool = True,
    ) -> None: ...
