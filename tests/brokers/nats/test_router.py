import asyncio

import pytest

from faststream.nats import NatsRoute, NatsRouter
from tests.brokers.base.router import RouterLocalTestcase, RouterTestcase


@pytest.mark.nats
class TestRouter(RouterTestcase):
    broker_class = NatsRouter
    route_class = NatsRoute

    async def test_delayed_handlers_with_queue(
        self,
        event,
        router: NatsRouter,
        queue: str,
        pub_broker,
    ):
        def response(m):
            event.set()

        r = type(router)(
            prefix="test.", handlers=(self.route_class(response, subject=queue),)
        )

        pub_broker.include_router(r)

        await pub_broker.start()

        await asyncio.wait(
            (
                asyncio.create_task(pub_broker.publish("hello", f"test.{queue}")),
                asyncio.create_task(event.wait()),
            ),
            timeout=3,
        )

        assert event.is_set()


class TestRouterLocal(RouterLocalTestcase):
    broker_class = NatsRouter
    route_class = NatsRoute
