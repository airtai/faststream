import pytest
from unittest.mock import patch

from faststream.nats import NatsBroker
from tests.tools import spy_decorator


@pytest.mark.asyncio()
async def test_object_storage_cache():
    broker = NatsBroker()
    await broker.connect()

    with patch.object(NatsBroker, "object_storage", spy_decorator(NatsBroker.object_storage)) as m:
        await broker.object_storage("test")
        assert broker._os_declarer.buckets["test"]
        m.mock.assert_called_once()
