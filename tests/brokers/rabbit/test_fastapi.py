import pytest

from faststream.rabbit import ExchangeType, RabbitExchange, RabbitQueue
from faststream.rabbit.fastapi import RabbitRouter
from faststream.rabbit.test import TestRabbitBroker, build_message
from tests.brokers.base.fastapi import FastAPILocalTestcase, FastAPITestcase


@pytest.mark.rabbit
class TestRouter(FastAPITestcase):
    router_class = RabbitRouter


class TestRouterLocal(FastAPILocalTestcase):
    router_class = RabbitRouter
    broker_test = staticmethod(TestRabbitBroker)
    build_message = staticmethod(build_message)

    @pytest.mark.asyncio
    async def test_path(self):
        router = self.router_class()

        @router.subscriber(
            RabbitQueue(
                "",
                routing_key="in.{name}",
            ),
            RabbitExchange(
                "test",
                type=ExchangeType.TOPIC,
            ),
        )
        async def hello(name):
            return name

        async with self.broker_test(router.broker):
            r = await router.broker.publish(
                "hi",
                "in.john",
                "test",
                rpc=True,
                rpc_timeout=0.5,
            )
            assert r == "john"
