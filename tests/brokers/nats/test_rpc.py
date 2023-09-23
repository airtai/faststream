import pytest

from faststream.nats import JsStream, NatsBroker
from tests.brokers.base.rpc import BrokerRPCTestcase, ReplyAndConsumeForbidden


@pytest.mark.nats
class TestRPC(BrokerRPCTestcase, ReplyAndConsumeForbidden):
    @pytest.mark.asyncio
    async def test_rpc_js(self, queue: str, rpc_broker: NatsBroker, stream: JsStream):
        @rpc_broker.subscriber(queue, stream=stream)
        async def m(m):  # pragma: no cover
            return "1"

        await rpc_broker.start()

        r = await rpc_broker.publish(
            "hello", queue, rpc_timeout=3, stream=stream.name, rpc=True
        )
        assert r == "1"
