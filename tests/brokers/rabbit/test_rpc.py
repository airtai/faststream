import asyncio
import uuid

import anyio
import pytest

from faststream.rabbit import RabbitBroker
from faststream.rabbit.publisher.producer import _RPCManager
from tests.brokers.base.rpc import BrokerRPCTestcase, ReplyAndConsumeForbidden


@pytest.mark.rabbit()
class TestRPC(BrokerRPCTestcase, ReplyAndConsumeForbidden):
    def get_broker(self, apply_types: bool = False) -> RabbitBroker:
        return RabbitBroker(apply_types=apply_types)

    @pytest.mark.asyncio()
    async def test_rpc_with_concurrency(self, queue: str):
        rpc_broker = self.get_broker()

        @rpc_broker.subscriber(queue)
        async def m(m):  # pragma: no cover
            await asyncio.sleep(1)
            return m

        async with self.patch_broker(rpc_broker) as br:
            await br.start()

            with anyio.fail_after(3):
                results = await asyncio.gather(
                    *[
                        br.publish(
                            f"hello {i}",
                            queue,
                            rpc=True,
                        )
                        for i in range(10)
                    ]
                )

            for i, r in enumerate(results):
                assert r == f"hello {i}"


class TestRPCManager:
    @pytest.mark.asyncio()
    async def test_context_variables_per_concurrent_task(self):
        rpc_broker = RabbitBroker()
        rpc_manager = _RPCManager(declarer=rpc_broker.declarer)
        results = set()
        correlation_ids = set()
        channels = set()

        async def run_operation():
            context = await rpc_manager(correlation_id=uuid.uuid4().hex)
            async with context:
                results.add(rpc_manager.result)
                correlation_ids.add(rpc_manager.correlation_id)
                channels.add(rpc_manager.queue.channel)

        await rpc_broker.start()
        await asyncio.gather(*[run_operation() for _ in range(10)])
        assert len(results) == 10
        assert len(correlation_ids) == 10
        assert len(channels) == 1

    @pytest.mark.asyncio()
    async def test_one_queue_per_channel(self):
        rpc_broker = RabbitBroker(max_channel_pool_size=10)
        rpc_manager = _RPCManager(declarer=rpc_broker.declarer)
        channels = set()

        async def run_operation():
            context = await rpc_manager(correlation_id=uuid.uuid4().hex)
            async with context:
                channels.add(rpc_manager.queue)

        await rpc_broker.start()
        await asyncio.gather(*[run_operation() for _ in range(10)])
        assert len(channels) == 10

    @pytest.mark.asyncio()
    async def test_clean_up_after_exception(self):
        rpc_broker = RabbitBroker()
        rpc_manager = _RPCManager(declarer=rpc_broker.declarer)

        await rpc_broker.start()
        with pytest.raises(ValueError):  # noqa: PT011
            async with await rpc_manager(correlation_id=uuid.uuid4().hex):
                raise ValueError("test")

        assert len(rpc_manager._RPCManager__rpc_messages) == 0
        assert not rpc_manager.queue._consumers
