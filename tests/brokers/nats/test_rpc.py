import pytest

from faststream.nats import JStream, NatsBroker
from tests.brokers.base.rpc import BrokerRPCTestcase, ReplyAndConsumeForbidden


@pytest.mark.nats
class TestRPC(BrokerRPCTestcase, ReplyAndConsumeForbidden):
    def get_broker(self, apply_types: bool = False) -> NatsBroker:
        return NatsBroker(apply_types=apply_types)

    @pytest.mark.asyncio
    async def test_rpc_js(self, queue: str, stream: JStream):
        rpc_broker = self.get_broker()

        @rpc_broker.subscriber(queue, stream=stream)
        async def m(m):  # pragma: no cover
            return "1"

        async with rpc_broker:
            await rpc_broker.start()

            r = await rpc_broker.publish(
                "hello", queue, rpc_timeout=3, stream=stream.name, rpc=True
            )
            assert r == "1"
