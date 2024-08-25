import asyncio
from abc import abstractstaticmethod
from typing import Any
from unittest.mock import MagicMock

import anyio
import pytest

from faststream.broker.core.usecase import BrokerUsecase
from faststream.utils.functions import timeout_scope

from .basic import BaseTestcaseConfig


class BrokerRPCTestcase(BaseTestcaseConfig):
    @abstractstaticmethod
    def get_broker(self, apply_types: bool = False) -> BrokerUsecase[Any, Any]:
        raise NotImplementedError

    def patch_broker(self, broker: BrokerUsecase[Any, Any]) -> BrokerUsecase[Any, Any]:
        return broker

    @pytest.mark.asyncio
    async def test_rpc(self, queue: str):
        rpc_broker = self.get_broker()

        args, kwargs = self.get_subscriber_params(queue)

        @rpc_broker.subscriber(*args, **kwargs)
        async def m(m):
            return "Hi!"

        async with self.patch_broker(rpc_broker) as br:
            await br.start()
            r = await br.publish("hello", queue, rpc_timeout=3, rpc=True)

        assert r == "Hi!"

    @pytest.mark.asyncio
    async def test_rpc_timeout_raises(self, queue: str):
        rpc_broker = self.get_broker()

        args, kwargs = self.get_subscriber_params(queue)

        @rpc_broker.subscriber(*args, **kwargs)
        async def m(m):  # pragma: no cover
            await anyio.sleep(1)

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

    @pytest.mark.asyncio
    async def test_rpc_timeout_none(self, queue: str):
        rpc_broker = self.get_broker()

        args, kwargs = self.get_subscriber_params(queue)

        @rpc_broker.subscriber(*args, **kwargs)
        async def m(m):  # pragma: no cover
            await anyio.sleep(1)

        async with self.patch_broker(rpc_broker) as br:
            await br.start()

            r = await br.publish(
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
        mock: MagicMock,
        event: asyncio.Event,
    ):
        rpc_broker = self.get_broker()

        reply_queue = queue + "1"

        args, kwargs = self.get_subscriber_params(reply_queue)

        @rpc_broker.subscriber(*args, **kwargs)
        async def response_hanler(m: str):
            mock(m)
            event.set()

        args2, kwargs2 = self.get_subscriber_params(queue)

        @rpc_broker.subscriber(*args2, **kwargs2)
        async def m(m):
            return "1"

        async with self.patch_broker(rpc_broker) as br:
            await br.start()

            await br.publish("hello", queue, reply_to=reply_queue)

            with timeout_scope(3, True):
                await event.wait()

        mock.assert_called_with("1")


class ReplyAndConsumeForbidden:
    @pytest.mark.asyncio
    async def test_rpc_with_reply_and_callback(self):
        rpc_broker = self.get_broker()

        async with rpc_broker:
            with pytest.raises(ValueError):  # noqa: PT011
                await rpc_broker.publish(
                    "hello",
                    "some",
                    reply_to="some",
                    rpc=True,
                    rpc_timeout=0,
                )
