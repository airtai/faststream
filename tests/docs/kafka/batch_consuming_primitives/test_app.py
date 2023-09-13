import pytest

from docs.docs_src.kafka.batch_consuming_primitives.app import broker, handle_batch
from faststream.kafka import TestKafkaBroker


@pytest.mark.asyncio
async def test_me():
    async with TestKafkaBroker(broker):
        await broker.publish_batch("I", "am", "FastStream", topic="test_batch")
        handle_batch.mock.assert_called_with(["I", "am", "FastStream"])
