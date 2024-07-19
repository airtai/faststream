import asyncio

import anyio
import pytest

from faststream.rabbit import RabbitBroker
from faststream.rabbit.publisher.producer import _RPCManager
from tests.brokers.base.rpc import BrokerRPCTestcase, ReplyAndConsumeForbidden


@pytest.mark.rabbit()
class TestRPC(BrokerRPCTestcase, ReplyAndConsumeForbidden):
    def get_broker(
        self, apply_types: bool = False, max_channel_pool_size: int = 2
    ) -> RabbitBroker:
        return RabbitBroker(
            apply_types=apply_types, max_channel_pool_size=max_channel_pool_size
        )

    @pytest.mark.asyncio()
    async def test_rpc_with_concurrency(self, queue: str):
        rpc_broker = self.get_broker(max_channel_pool_size=20)

        @rpc_broker.subscriber(queue)
        async def m(m):  # pragma: no cover
            await asyncio.sleep(0.1)
            return m

        async with self.patch_broker(rpc_broker) as br:
            await br.start()

            with anyio.fail_after(1):
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

    @pytest.mark.asyncio()
    async def test_rpc_with_concurrency_equal_consumers_channels(self, queue: str):
        rpc_broker = self.get_broker(max_channel_pool_size=9)

        @rpc_broker.subscriber(queue)
        async def m(m):  # pragma: no cover
            await asyncio.sleep(0.1)
            return m

        async with self.patch_broker(rpc_broker) as br:
            await br.start()

            with anyio.fail_after(1):
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

    @pytest.mark.asyncio()
    async def test_rpc_recovers_after_timeout(self, queue: str):
        rpc_broker = self.get_broker()

        @rpc_broker.subscriber(queue)
        async def m(m):  # pragma: no cover
            await anyio.sleep(0.1)
            return m

        async with self.patch_broker(rpc_broker) as br:
            await br.start()

            with pytest.raises(TimeoutError):  # pragma: no branch
                await br.publish(
                    "hello",
                    queue,
                    rpc=True,
                    rpc_timeout=0,
                    raise_timeout=True,
                )
            assert (
                await br.publish(
                    "hello",
                    queue,
                    rpc=True,
                )
            ) == "hello"


class TestRPCManager:
    @pytest.mark.asyncio()
    async def test_context_variables_per_concurrent_task(self):
        rpc_broker = RabbitBroker(max_channel_pool_size=10)
        rpc_manager = _RPCManager(declarer=rpc_broker.declarer)
        receive_streams = set()
        channels = set()

        async def run_operation():
            async with rpc_manager() as (receive_stream, channel):
                receive_streams.add(receive_stream)
                channels.add(channel)
                await asyncio.sleep(0.1)

        async with rpc_broker:
            await asyncio.gather(*[run_operation() for _ in range(10)])
            assert len(receive_streams) == 10
            assert len(channels) == 10
