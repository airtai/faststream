import pytest

from faststream.nats.fastapi import NatsRouter
from faststream.nats.test import TestNatsBroker, build_message
from tests.brokers.base.fastapi import FastAPILocalTestcase, FastAPITestcase


@pytest.mark.nats
class TestRouter(FastAPITestcase):
    router_class = NatsRouter


class TestRouterLocal(FastAPILocalTestcase):
    router_class = NatsRouter
    broker_test = staticmethod(TestNatsBroker)
    build_message = staticmethod(build_message)

    @pytest.mark.asyncio
    async def test_path(self, queue: str):
        router = self.router_class()

        @router.subscriber(queue + ".{name}")
        async def hello(name):
            return name

        async with self.broker_test(router.broker):
            r = await router.broker.publish(
                "hi",
                f"{queue}.john",
                rpc=True,
                rpc_timeout=0.5,
            )
            assert r == "john"
