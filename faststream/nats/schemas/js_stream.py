from typing import TYPE_CHECKING, List, Optional

from nats.js.api import DiscardPolicy, StreamConfig

from faststream.broker.schemas import NameRequired

if TYPE_CHECKING:
    from nats.js.api import (
        Placement,
        RePublish,
        RetentionPolicy,
        StorageType,
        StreamSource,
    )

class JStream(NameRequired):
    """A class to represent a JetStream stream."""

    __slots__ = (
        "name",
        "config",
        "subjects",
        "declare",
    )

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        subjects: Optional[List[str]] = None,
        retention: Optional["RetentionPolicy"] = None,
        max_consumers: Optional[int] = None,
        max_msgs: Optional[int] = None,
        max_bytes: Optional[int] = None,
        discard: Optional["DiscardPolicy"] = DiscardPolicy.OLD,
        max_age: Optional[float] = None,  # in seconds
        max_msgs_per_subject: int = -1,
        max_msg_size: Optional[int] = -1,
        storage: Optional["StorageType"] = None,
        num_replicas: Optional[int] = None,
        no_ack: bool = False,
        template_owner: Optional[str] = None,
        duplicate_window: float = 0,
        placement: Optional["Placement"] = None,
        mirror: Optional["StreamSource"] = None,
        sources: Optional[List["StreamSource"]] = None,
        sealed: bool = False,
        deny_delete: bool = False,
        deny_purge: bool = False,
        allow_rollup_hdrs: bool = False,
        republish: Optional["RePublish"] = None,
        allow_direct: Optional[bool] = None,
        mirror_direct: Optional[bool] = None,
        # custom
        declare: bool = True,
    ) -> None:
        """Initialize the JetStream stream."""
        super().__init__(name)

        subjects = subjects or []

        self.subjects = subjects
        self.declare = declare
        self.config = StreamConfig(
            name=name,
            description=description,
            retention=retention,
            max_consumers=max_consumers,
            max_msgs=max_msgs,
            max_bytes=max_bytes,
            discard=discard,
            max_age=max_age,
            max_msgs_per_subject=max_msgs_per_subject,
            max_msg_size=max_msg_size,
            storage=storage,
            num_replicas=num_replicas,
            no_ack=no_ack,
            template_owner=template_owner,
            duplicate_window=duplicate_window,
            placement=placement,
            mirror=mirror,
            sources=sources,
            sealed=sealed,
            deny_delete=deny_delete,
            deny_purge=deny_purge,
            allow_rollup_hdrs=allow_rollup_hdrs,
            republish=republish,
            allow_direct=allow_direct,
            mirror_direct=mirror_direct,
            subjects=[],  # use self.subjects in declaration
        )

    def add_subject(self, subject: str) -> None:
        if subject not in self.subjects:
            self.subjects.append(subject)
