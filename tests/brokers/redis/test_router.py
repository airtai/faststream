import asyncio

import pytest

from faststream import Path
from faststream.redis import RedisBroker, RedisPublisher, RedisRoute, RedisRouter
from tests.brokers.base.router import RouterLocalTestcase, RouterTestcase


@pytest.mark.redis
class TestRouter(RouterTestcase):
    broker_class = RedisRouter
    route_class = RedisRoute
    publisher_class = RedisPublisher


class TestRouterLocal(RouterLocalTestcase):
    broker_class = RedisRouter
    route_class = RedisRoute
    publisher_class = RedisPublisher

    async def test_router_path(
        self,
        event,
        mock,
        router,
        pub_broker,
    ):
        @router.subscriber("in.{name}.{id}")
        async def h(
            name: str = Path(),
            id: int = Path("id"),
        ):
            event.set()
            mock(name=name, id=id)

        pub_broker._is_apply_types = True
        pub_broker.include_router(router)

        await pub_broker.start()

        await pub_broker.publish(
            "",
            "in.john.2",
            rpc=True,
        )

        assert event.is_set()
        mock.assert_called_once_with(name="john", id=2)

    async def test_router_path_with_prefix(
        self,
        event,
        mock,
        router,
        pub_broker,
    ):
        router.prefix = "test."

        @router.subscriber("in.{name}.{id}")
        async def h(
            name: str = Path(),
            id: int = Path("id"),
        ):
            event.set()
            mock(name=name, id=id)

        pub_broker._is_apply_types = True
        pub_broker.include_router(router)

        await pub_broker.start()

        await pub_broker.publish(
            "",
            "test.in.john.2",
            rpc=True,
        )

        assert event.is_set()
        mock.assert_called_once_with(name="john", id=2)

    async def test_router_delay_handler_path(
        self,
        event,
        mock,
        router,
        pub_broker,
    ):
        async def h(
            name: str = Path(),
            id: int = Path("id"),
        ):
            event.set()
            mock(name=name, id=id)

        r = type(router)(handlers=(self.route_class(h, channel="in.{name}.{id}"),))

        pub_broker._is_apply_types = True
        pub_broker.include_router(r)

        await pub_broker.start()

        await pub_broker.publish(
            "",
            "in.john.2",
            rpc=True,
        )

        assert event.is_set()
        mock.assert_called_once_with(name="john", id=2)

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
