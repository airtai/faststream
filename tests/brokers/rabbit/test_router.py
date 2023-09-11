import asyncio

import pytest

from faststream.rabbit import RabbitBroker, RabbitQueue, RabbitRoute, RabbitRouter
from tests.brokers.base.router import RouterLocalTestcase, RouterTestcase


@pytest.mark.rabbit
class TestRouter(RouterTestcase):
    broker_class = RabbitRouter
    route_class = RabbitRoute

    async def test_queue_obj(
        self,
        router: RabbitRouter,
        broker: RabbitBroker,
        queue: str,
        event: asyncio.Event,
    ):
        router.prefix = "test/"

        r_queue = RabbitQueue(queue)

        @router.subscriber(r_queue)
        def subscriber(m):
            event.set()

        broker.include_router(router)

        await broker.start()

        await asyncio.wait(
            (
                asyncio.create_task(broker.publish("hello", f"test/{r_queue.name}")),
                asyncio.create_task(event.wait()),
            ),
            timeout=3,
        )

        assert event.is_set()

    async def test_delayed_handlers_with_queue(
        self,
        event: asyncio.Event,
        router: RabbitRouter,
        queue: str,
        pub_broker: RabbitBroker,
    ):
        def response(m):
            event.set()

        r_queue = RabbitQueue(queue)

        r = type(router)(
            prefix="test/", handlers=(self.route_class(response, r_queue),)
        )

        pub_broker.include_router(r)

        await pub_broker.start()

        await asyncio.wait(
            (
                asyncio.create_task(
                    pub_broker.publish("hello", f"test/{r_queue.name}")
                ),
                asyncio.create_task(event.wait()),
            ),
            timeout=3,
        )

        assert event.is_set()


class TestRouterLocal(RouterLocalTestcase):
    broker_class = RabbitRouter
    route_class = RabbitRoute
