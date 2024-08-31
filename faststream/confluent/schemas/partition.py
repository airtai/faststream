from typing import Optional

from confluent_kafka import TopicPartition as ConfluentPartition
from typing_extensions import NotRequired, TypedDict


class _TopicKwargs(TypedDict):
    topic: str
    partition: int
    offset: int
    metadata: NotRequired[str]
    leader_epoch: NotRequired[int]


class TopicPartition:
    __slots__ = (
        "topic",
        "partition",
        "offset",
        "metadata",
        "leader_epoch",
    )

    def __init__(
        self,
        topic: str,
        partition: int = -1,
        offset: int = -1001,
        metadata: Optional[str] = None,
        leader_epoch: Optional[int] = None,
    ) -> None:
        self.topic = topic
        self.partition = partition
        self.offset = offset
        self.metadata = metadata
        self.leader_epoch = leader_epoch

    def to_confluent(self) -> ConfluentPartition:
        kwargs: _TopicKwargs = {
            "topic": self.topic,
            "partition": self.partition,
            "offset": self.offset,
        }
        if self.metadata is not None:
            kwargs["metadata"] = self.metadata
        if self.leader_epoch is not None:
            kwargs["leader_epoch"] = self.leader_epoch
        return ConfluentPartition(**kwargs)
