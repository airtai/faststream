import asyncio
from unittest.mock import MagicMock

import anyio
import pytest

from faststream.broker.core.abc import BrokerUsecase
from faststream.utils.functions import timeout_scope


class BrokerRPCTestcase:
    @pytest.fixture
    def rpc_broker(self, broker):
        return broker

    @pytest.mark.asyncio
    async def test_rpc(self, queue: str, rpc_broker: BrokerUsecase):
        @rpc_broker.subscriber(queue)
        async def m(m):  # pragma: no cover
            return "1"

        await rpc_broker.start()

        r = await rpc_broker.publish("hello", queue, rpc_timeout=3, rpc=True)
        assert r == "1"

    @pytest.mark.asyncio
    async def test_rpc_timeout_raises(self, queue: str, rpc_broker: BrokerUsecase):
        @rpc_broker.subscriber(queue)
        async def m(m):  # pragma: no cover
            await anyio.sleep(1)

        await rpc_broker.start()

        with pytest.raises(TimeoutError):  # pragma: no branch
            await rpc_broker.publish(
                "hello",
                queue,
                rpc=True,
                rpc_timeout=0,
                raise_timeout=True,
            )

    @pytest.mark.asyncio
    async def test_rpc_timeout_none(self, queue: str, rpc_broker: BrokerUsecase):
        @rpc_broker.subscriber(queue)
        async def m(m):  # pragma: no cover
            await anyio.sleep(1)

        await rpc_broker.start()

        r = await rpc_broker.publish(
            "hello",
            queue,
            rpc=True,
            rpc_timeout=0,
        )

        assert r is None

    @pytest.mark.asyncio
    async def test_rpc_with_reply(
        self,
        queue: str,
        rpc_broker: BrokerUsecase,
        mock: MagicMock,
        event: asyncio.Event,
    ):
        reply_queue = queue + "1"

        @rpc_broker.subscriber(reply_queue)
        async def response_hanler(m: str):
            mock(m)
            event.set()

        @rpc_broker.subscriber(queue)
        async def m(m):  # pragma: no cover
            return "1"

        await rpc_broker.start()

        await rpc_broker.publish("hello", queue, reply_to=reply_queue)

        with timeout_scope(3, True):
            await event.wait()

        mock.assert_called_with("1")


class ReplyAndConsumeForbidden:
    @pytest.mark.asyncio
    async def test_rpc_with_reply_and_callback(self, full_broker: BrokerUsecase):
        with pytest.raises(ValueError):
            await full_broker.publish(
                "hello",
                "some",
                reply_to="some",
                rpc=True,
                rpc_timeout=0,
            )
