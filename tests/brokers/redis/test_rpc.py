import pytest

from faststream.redis import RedisBroker
from tests.brokers.base.rpc import BrokerRPCTestcase, ReplyAndConsumeForbidden


@pytest.mark.redis
class TestRPC(BrokerRPCTestcase, ReplyAndConsumeForbidden):
    def get_broker(self, apply_types: bool = False):
        return RedisBroker(apply_types=apply_types)

    @pytest.mark.asyncio
    async def test_list_rpc(self, queue: str):
        rpc_broker = self.get_broker()

        @rpc_broker.subscriber(list=queue)
        async def m(m):  # pragma: no cover
            return "1"

        async with self.patch_broker(rpc_broker) as br:
            await br.start()

            r = await br.publish("hello", list=queue, rpc_timeout=3, rpc=True)

        assert r == "1"
