import pytest

from faststream.kafka import TestKafkaBroker

from .app import broker, handle_batch


@pytest.mark.asyncio
async def test_me():
    async with TestKafkaBroker(broker):
        await broker.publish_batch("I", "am", "FastStream", topic="test_batch")
        handle_batch.mock.assert_called_with(["I", "am", "FastStream"])
