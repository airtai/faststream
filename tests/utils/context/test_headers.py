import pytest

from faststream import Header
from tests.marks import require_nats


@pytest.mark.asyncio
@require_nats
async def test_nats_headers():
    from faststream.nats import NatsBroker, TestNatsBroker

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
        assert (
            await br.publish(
                "",
                "in",
                headers={
                    "name": "john",
                    "id": "1",
                },
                rpc=True,
                rpc_timeout=1.0,
            )
            == 1
        )
