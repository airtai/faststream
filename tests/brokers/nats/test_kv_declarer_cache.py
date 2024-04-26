import pytest

from faststream.nats import NatsBroker


@pytest.mark.asyncio()
async def test_object_storage_cache():
    broker = NatsBroker()
    await broker.connect()
    bucket = await broker.key_value("test")
    assert bucket == broker._kv_declarer.buckets["test"]
