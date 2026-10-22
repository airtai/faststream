from dataclasses import dataclass, field

import pytest

from faststream.confluent.message import KafkaMessage


@dataclass
class Record:
    topic_: str
    partition_: int
    offset_: int

    def topic(self) -> str:
        return self.topic_

    def partition(self) -> int:
        return self.partition_

    def offset(self) -> int:
        return self.offset_


@dataclass
class Consumer:
    seeks: list[tuple[str, int, int]] = field(default_factory=list)

    async def commit(self) -> None:
        pass

    async def seek(self, topic: str, partition: int, offset: int) -> None:
        self.seeks.append((topic, partition, offset))


@pytest.mark.confluent()
@pytest.mark.asyncio()
async def test_batch_nack_rewinds_every_partition() -> None:
    consumer = Consumer()
    batch = (
        Record("t", 0, 1),
        Record("t", 0, 2),
        Record("t", 1, 0),
        Record("t", 1, 1),
        Record("t", 2, 5),
        Record("t", 2, 4),
    )
    message = KafkaMessage(batch, body=b"", consumer=consumer, is_manual=True)

    await message.nack()

    assert sorted(consumer.seeks) == [("t", 0, 1), ("t", 1, 0), ("t", 2, 4)]


@pytest.mark.confluent()
@pytest.mark.asyncio()
async def test_single_message_nack_rewinds_its_partition() -> None:
    consumer = Consumer()
    message = KafkaMessage(Record("t", 3, 7), body=b"", consumer=consumer, is_manual=True)

    await message.nack()

    assert consumer.seeks == [("t", 3, 7)]
