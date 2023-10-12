import pytest

from faststream import Header
from faststream.nats import NatsBroker, TestNatsBroker


@pytest.mark.asyncio
async def test_nats_headers():
    broker = NatsBroker()

    @broker.subscriber("in")
    async def h(
        name: str = Header(),
        id_: int = Header("id"),
    ):
        assert name == "john"
        assert id_ == 1
        return 1

    async with TestNatsBroker(broker) as br:
        assert 1 == await br.publish(
            "",
            "in",
            headers={
                "name": "john",
                "id": "1",
            },
            rpc=True,
            rpc_timeout=1.0,
        )
