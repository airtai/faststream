from typing import Optional

from confluent_kafka import TopicPartition as ConfluentPartition


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
        kwargs = {
            "topic": self.topic,
            "partition": self.partition,
            "offset": self.offset,
        }
        if self.metadata is not None:
            kwargs["metadata"] = self.metadata
        if self.leader_epoch is not None:
            kwargs["leader_epoch"] = self.leader_epoch
        return ConfluentPartition(**kwargs)  # type: ignore[arg-type]
