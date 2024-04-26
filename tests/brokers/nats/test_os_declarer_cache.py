import pytest

from faststream.nats import NatsBroker


@pytest.mark.asyncio()
async def test_object_storage_cache():
    broker = NatsBroker()
    await broker.connect()
    bucket = await broker.object_storage("test")
    assert bucket == broker._os_declarer.buckets["test"]
