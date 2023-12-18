import pytest

from faststream.redis import TestRedisBroker
from tests.marks import python310


@pytest.mark.asyncio
@python310
async def test_stream_sub():
    from docs.docs_src.redis.stream.batch_sub import broker, handle

    async with TestRedisBroker(broker) as br:
        await br.publish("Hi!", stream="test-stream")
        handle.mock.assert_called_once_with(["Hi!"])
