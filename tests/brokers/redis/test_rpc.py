import pytest

from faststream.redis import RedisBroker
from tests.brokers.base.rpc import BrokerRPCTestcase, ReplyAndConsumeForbidden


@pytest.mark.redis
class TestRPC(BrokerRPCTestcase, ReplyAndConsumeForbidden):
    @pytest.mark.asyncio
    async def test_list_rpc(self, queue: str, rpc_broker: RedisBroker):
        @rpc_broker.subscriber(list=queue)
        async def m(m):  # pragma: no cover
            return "1"

        async with rpc_broker:
            await rpc_broker.start()
            r = await rpc_broker.publish("hello", list=queue, rpc_timeout=3, rpc=True)

        assert r == "1"
