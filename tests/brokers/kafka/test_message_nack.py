from dataclasses import dataclass, field

import pytest
from aiokafka import TopicPartition

from faststream.kafka.message import KafkaAckableMessage


@dataclass
class Record:
    topic: str
    partition: int
    offset: int


@dataclass
class Consumer:
    seeks: list[tuple[TopicPartition, int]] = field(default_factory=list)

    async def commit(self) -> None:
        pass

    def seek(self, partition: TopicPartition, offset: int) -> None:
        self.seeks.append((partition, offset))


@pytest.mark.kafka()
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
    message = KafkaAckableMessage(batch, body=b"", consumer=consumer)

    await message.nack()

    assert sorted(consumer.seeks) == [
        (TopicPartition("t", 0), 1),
        (TopicPartition("t", 1), 0),
        (TopicPartition("t", 2), 4),
    ]


@pytest.mark.kafka()
@pytest.mark.asyncio()
async def test_single_message_nack_rewinds_its_partition() -> None:
    consumer = Consumer()
    message = KafkaAckableMessage(Record("t", 3, 7), body=b"", consumer=consumer)

    await message.nack()

    assert consumer.seeks == [(TopicPartition("t", 3), 7)]
