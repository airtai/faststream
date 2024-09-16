import asyncio

import pytest

from faststream import Path
from faststream.nats import JStream, NatsBroker, NatsPublisher, NatsRoute, NatsRouter
from tests.brokers.base.router import RouterLocalTestcase, RouterTestcase


@pytest.mark.nats
class TestRouter(RouterTestcase):
    broker_class = NatsRouter
    route_class = NatsRoute
    publisher_class = NatsPublisher

    async def test_router_path(
        self,
        event,
        mock,
        router: NatsRouter,
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

        await pub_broker.request("", "in.john.2")

        assert event.is_set()
        mock.assert_called_once_with(name="john", id=2)

    async def test_path_as_first_with_prefix(
        self,
        event,
        mock,
        router: NatsRouter,
        pub_broker,
    ):
        router.prefix = "root."

        @router.subscriber("{name}.nested")
        async def h(name: str = Path()):
            event.set()
            mock(name=name)

        pub_broker._is_apply_types = True
        pub_broker.include_router(router)

        await pub_broker.start()

        await pub_broker.request("", "root.john.nested")

        assert event.is_set()
        mock.assert_called_once_with(name="john")

    async def test_router_path_with_prefix(
        self,
        event,
        mock,
        router: NatsRouter,
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

        await pub_broker.request("", "test.in.john.2")

        assert event.is_set()
        mock.assert_called_once_with(name="john", id=2)

    async def test_router_delay_handler_path(
        self,
        event,
        mock,
        router: NatsRouter,
        pub_broker,
    ):
        async def h(
            name: str = Path(),
            id: int = Path("id"),
        ):
            event.set()
            mock(name=name, id=id)

        r = type(router)(handlers=(self.route_class(h, subject="in.{name}.{id}"),))

        pub_broker._is_apply_types = True
        pub_broker.include_router(r)

        await pub_broker.start()

        await pub_broker.request("", "in.john.2")

        assert event.is_set()
        mock.assert_called_once_with(name="john", id=2)

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
    publisher_class = NatsPublisher

    async def test_include_stream(
        self,
        router: NatsRouter,
        pub_broker: NatsBroker,
    ):
        @router.subscriber("test", stream="stream")
        async def handler(): ...

        pub_broker.include_router(router)

        assert next(iter(pub_broker._stream_builder.objects.keys())) == "stream"

    async def test_include_stream_with_subjects(self):
        stream = JStream("test-stream")

        sub_router = NatsRouter(prefix="client.")

        sub_router.subscriber("1", stream=stream)
        sub_router.subscriber("2", stream=stream)

        router = NatsRouter(prefix="user.")

        router.subscriber("registered", stream=stream)

        router.include_router(sub_router)

        broker = NatsBroker()
        broker.include_router(router)

        assert set(stream.subjects) == {
            "user.registered",
            "user.client.1",
            "user.client.2",
        }
