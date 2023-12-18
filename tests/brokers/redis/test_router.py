import asyncio

import pytest

from faststream.redis import RedisBroker, RedisRoute, RedisRouter
from tests.brokers.base.router import RouterLocalTestcase, RouterTestcase


@pytest.mark.redis
class TestRouter(RouterTestcase):
    broker_class = RedisRouter
    route_class = RedisRoute


class TestRouterLocal(RouterLocalTestcase):
    broker_class = RedisRouter
    route_class = RedisRoute

    async def test_delayed_channel_handlers(
        self,
        event: asyncio.Event,
        queue: str,
        pub_broker: RedisBroker,
    ):
        def response(m):
            event.set()

        r = RedisRouter(prefix="test_", handlers=(RedisRoute(response, channel=queue),))

        pub_broker.include_router(r)

        async with pub_broker:
            await pub_broker.start()

            await asyncio.wait(
                (
                    asyncio.create_task(
                        pub_broker.publish("hello", channel=f"test_{queue}")
                    ),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

            assert event.is_set()

    async def test_delayed_list_handlers(
        self,
        event: asyncio.Event,
        queue: str,
        pub_broker: RedisBroker,
    ):
        def response(m):
            event.set()

        r = RedisRouter(prefix="test_", handlers=(RedisRoute(response, list=queue),))

        pub_broker.include_router(r)

        async with pub_broker:
            await pub_broker.start()

            await asyncio.wait(
                (
                    asyncio.create_task(
                        pub_broker.publish("hello", list=f"test_{queue}")
                    ),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

            assert event.is_set()

    async def test_delayed_stream_handlers(
        self,
        event: asyncio.Event,
        queue: str,
        pub_broker: RedisBroker,
    ):
        def response(m):
            event.set()

        r = RedisRouter(prefix="test_", handlers=(RedisRoute(response, stream=queue),))

        pub_broker.include_router(r)

        async with pub_broker:
            await pub_broker.start()

            await asyncio.wait(
                (
                    asyncio.create_task(
                        pub_broker.publish("hello", stream=f"test_{queue}")
                    ),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

            assert event.is_set()
