import pytest
from unittest.mock import patch

from faststream.nats import NatsBroker
from tests.tools import spy_decorator


@pytest.mark.asyncio()
async def test_kv_storage_cache():
    broker = NatsBroker()
    await broker.connect()

    with patch.object(NatsBroker, "key_value", spy_decorator(NatsBroker.key_value)) as m:
        await broker.key_value("test")
        assert broker._kv_declarer.buckets["test"]
        m.mock.assert_called_once()
