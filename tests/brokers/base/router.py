import asyncio
from typing import Type
from unittest.mock import Mock

import pytest

from faststream import BaseMiddleware, Depends
from faststream.broker.core.asyncronous import BrokerAsyncUsecase
from faststream.broker.router import BrokerRoute, BrokerRouter
from faststream.types import AnyCallable
from tests.brokers.base.middlewares import LocalMiddlewareTestcase
from tests.brokers.base.parser import LocalCustomParserTestcase


@pytest.mark.asyncio
class RouterTestcase(LocalMiddlewareTestcase, LocalCustomParserTestcase):
    build_message: AnyCallable
    route_class: Type[BrokerRoute]

    def patch_broker(
        self, br: BrokerAsyncUsecase, router: BrokerRouter
    ) -> BrokerAsyncUsecase:
        br.include_router(router)
        return br

    @pytest.fixture
    def pub_broker(self, broker):
        return broker

    @pytest.fixture
    def raw_broker(self, pub_broker):
        return pub_broker

    async def test_empty_prefix(
        self,
        router: BrokerRouter,
        pub_broker: BrokerAsyncUsecase,
        queue: str,
        event: asyncio.Event,
    ):
        @router.subscriber(queue)
        def subscriber(m):
            event.set()

        pub_broker.include_router(router)

        await pub_broker.start()

        await asyncio.wait(
            (
                asyncio.create_task(pub_broker.publish("hello", queue)),
                asyncio.create_task(event.wait()),
            ),
            timeout=3,
        )

        assert event.is_set()

    async def test_not_empty_prefix(
        self,
        router: BrokerRouter,
        pub_broker: BrokerAsyncUsecase,
        queue: str,
        event: asyncio.Event,
    ):
        router.prefix = "test_"

        @router.subscriber(queue)
        def subscriber(m):
            event.set()

        pub_broker.include_router(router)

        await pub_broker.start()

        await asyncio.wait(
            (
                asyncio.create_task(pub_broker.publish("hello", f"test_{queue}")),
                asyncio.create_task(event.wait()),
            ),
            timeout=3,
        )

        assert event.is_set()

    async def test_empty_prefix_publisher(
        self,
        router: BrokerRouter,
        pub_broker: BrokerAsyncUsecase,
        queue: str,
        event: asyncio.Event,
    ):
        @router.subscriber(queue)
        @router.publisher(queue + "resp")
        def subscriber(m):
            return "hi"

        @router.subscriber(queue + "resp")
        def response(m):
            event.set()

        pub_broker.include_router(router)

        await pub_broker.start()

        await asyncio.wait(
            (
                asyncio.create_task(pub_broker.publish("hello", queue)),
                asyncio.create_task(event.wait()),
            ),
            timeout=3,
        )

        assert event.is_set()

    async def test_not_empty_prefix_publisher(
        self,
        router: BrokerRouter,
        pub_broker: BrokerAsyncUsecase,
        queue: str,
        event: asyncio.Event,
    ):
        router.prefix = "test_"

        @router.subscriber(queue)
        @router.publisher(queue + "resp")
        def subscriber(m):
            return "hi"

        @router.subscriber(queue + "resp")
        def response(m):
            event.set()

        pub_broker.include_router(router)

        await pub_broker.start()

        await asyncio.wait(
            (
                asyncio.create_task(pub_broker.publish("hello", f"test_{queue}")),
                asyncio.create_task(event.wait()),
            ),
            timeout=3,
        )

        assert event.is_set()

    async def test_manual_publisher(
        self,
        router: BrokerRouter,
        pub_broker: BrokerAsyncUsecase,
        queue: str,
        event: asyncio.Event,
    ):
        router.prefix = "test_"

        p = router.publisher(queue + "resp")

        @router.subscriber(queue)
        async def subscriber(m):
            await p.publish("resp")

        @router.subscriber(queue + "resp")
        def response(m):
            event.set()

        pub_broker.include_router(router)

        await pub_broker.start()

        await asyncio.wait(
            (
                asyncio.create_task(pub_broker.publish("hello", f"test_{queue}")),
                asyncio.create_task(event.wait()),
            ),
            timeout=3,
        )

        assert event.is_set()

    async def test_delayed_handlers(
        self,
        event: asyncio.Event,
        router: BrokerRouter,
        queue: str,
        pub_broker: BrokerAsyncUsecase,
    ):
        def response(m):
            event.set()

        r = type(router)(prefix="test_", handlers=(self.route_class(response, queue),))

        pub_broker.include_router(r)

        await pub_broker.start()

        await asyncio.wait(
            (
                asyncio.create_task(pub_broker.publish("hello", f"test_{queue}")),
                asyncio.create_task(event.wait()),
            ),
            timeout=3,
        )

        assert event.is_set()

    async def test_nested_routers_sub(
        self,
        router: BrokerRouter,
        pub_broker: BrokerAsyncUsecase,
        queue: str,
        event: asyncio.Event,
        mock: Mock,
    ):
        core_router = type(router)(prefix="test1_")
        router.prefix = "test2_"

        @router.subscriber(queue)
        def subscriber(m):
            event.set()
            mock(m)
            return "hi"

        core_router.include_routers(router)
        pub_broker.include_routers(core_router)

        await pub_broker.start()

        await asyncio.wait(
            (
                asyncio.create_task(
                    pub_broker.publish("hello", f"test1_test2_{queue}")
                ),
                asyncio.create_task(event.wait()),
            ),
            timeout=3,
        )

        assert event.is_set()
        mock.assert_called_with("hello")

    async def test_nested_routers_pub(
        self,
        router: BrokerRouter,
        pub_broker: BrokerAsyncUsecase,
        queue: str,
        event: asyncio.Event,
    ):
        core_router = type(router)(prefix="test1_")
        router.prefix = "test2_"

        @router.subscriber(queue)
        @router.publisher(queue + "resp")
        def subscriber(m):
            return "hi"

        @pub_broker.subscriber("test1_" + "test2_" + queue + "resp")
        def response(m):
            event.set()

        core_router.include_routers(router)
        pub_broker.include_routers(core_router)

        await pub_broker.start()

        await asyncio.wait(
            (
                asyncio.create_task(
                    pub_broker.publish("hello", f"test1_test2_{queue}")
                ),
                asyncio.create_task(event.wait()),
            ),
            timeout=3,
        )

        assert event.is_set()

    async def test_router_dependencies(
        self,
        router: BrokerRouter,
        pub_broker: BrokerAsyncUsecase,
        queue: str,
        event: asyncio.Event,
        mock: Mock,
    ):
        pub_broker._is_apply_types = True

        async def dep1(s):
            mock.dep1()

        async def dep2(s):
            mock.dep1.assert_called_once()
            mock.dep2()

        router = type(router)(dependencies=(Depends(dep1),))

        @router.subscriber(queue, dependencies=(Depends(dep2),))
        def subscriber(s):
            event.set()

        pub_broker.include_routers(router)

        await pub_broker.start()

        await asyncio.wait(
            (
                asyncio.create_task(pub_broker.publish("hello", queue)),
                asyncio.create_task(event.wait()),
            ),
            timeout=3,
        )

        assert event.is_set()
        mock.dep1.assert_called_once()
        mock.dep2.assert_called_once()

    async def test_router_middlewares(
        self,
        router: BrokerRouter,
        pub_broker: BrokerAsyncUsecase,
        queue: str,
        event: asyncio.Event,
        mock: Mock,
    ):
        class mid1(BaseMiddleware):
            async def on_receive(self) -> None:
                mock.mid1()

        class mid2(BaseMiddleware):
            async def on_receive(self) -> None:
                mock.mid1.assert_called_once()
                mock.mid2()

        router = type(router)(middlewares=(mid1,))

        @router.subscriber(queue, middlewares=(mid2,))
        def subscriber(s):
            event.set()

        pub_broker.include_routers(router)

        await pub_broker.start()

        await asyncio.wait(
            (
                asyncio.create_task(pub_broker.publish("hello", queue)),
                asyncio.create_task(event.wait()),
            ),
            timeout=3,
        )

        assert event.is_set()
        mock.mid1.assert_called_once()
        mock.mid2.assert_called_once()

    async def test_router_parser(
        self,
        router: BrokerRouter,
        pub_broker: BrokerAsyncUsecase,
        queue: str,
        event: asyncio.Event,
        mock: Mock,
    ):
        async def parser(msg, original):
            mock.parser()
            return await original(msg)

        async def decoder(msg, original):
            mock.decoder()
            return await original(msg)

        router = type(router)(
            parser=parser,
            decoder=decoder,
        )

        @router.subscriber(queue)
        def subscriber(s):
            event.set()

        pub_broker.include_routers(router)

        await pub_broker.start()

        await asyncio.wait(
            (
                asyncio.create_task(pub_broker.publish("hello", queue)),
                asyncio.create_task(event.wait()),
            ),
            timeout=3,
        )

        assert event.is_set()
        mock.parser.assert_called_once()
        mock.decoder.assert_called_once()

    async def test_router_parser_override(
        self,
        router: BrokerRouter,
        pub_broker: BrokerAsyncUsecase,
        queue: str,
        event: asyncio.Event,
        mock: Mock,
    ):
        async def global_parser(msg, original):  # pragma: no cover
            mock()
            return await original(msg)

        async def global_decoder(msg, original):  # pragma: no cover
            mock()
            return await original(msg)

        async def parser(msg, original):
            mock.parser()
            return await original(msg)

        async def decoder(msg, original):
            mock.decoder()
            return await original(msg)

        router = type(router)(
            parser=global_parser,
            decoder=global_decoder,
        )

        @router.subscriber(queue, parser=parser, decoder=decoder)
        def subscriber(s):
            event.set()

        pub_broker.include_routers(router)

        await pub_broker.start()

        await asyncio.wait(
            (
                asyncio.create_task(pub_broker.publish("hello", queue)),
                asyncio.create_task(event.wait()),
            ),
            timeout=3,
        )

        assert event.is_set()
        assert not mock.called
        mock.parser.assert_called_once()
        mock.decoder.assert_called_once()


@pytest.mark.asyncio
class RouterLocalTestcase(RouterTestcase):
    @pytest.fixture
    def pub_broker(self, test_broker):
        return test_broker

    async def test_publisher_mock(
        self,
        router: BrokerRouter,
        pub_broker: BrokerAsyncUsecase,
        queue: str,
        event: asyncio.Event,
    ):
        pub = router.publisher(queue + "resp")

        @router.subscriber(queue)
        @pub
        def subscriber(m):
            event.set()
            return "hi"

        pub_broker.include_router(router)

        await pub_broker.start()

        await asyncio.wait(
            (
                asyncio.create_task(pub_broker.publish("hello", queue)),
                asyncio.create_task(event.wait()),
            ),
            timeout=3,
        )

        assert event.is_set()
        pub.mock.assert_called_with("hi")

    async def test_subscriber_mock(
        self,
        router: BrokerRouter,
        pub_broker: BrokerAsyncUsecase,
        queue: str,
        event: asyncio.Event,
    ):
        @router.subscriber(queue)
        def subscriber(m):
            event.set()
            return "hi"

        pub_broker.include_router(router)

        await pub_broker.start()

        await asyncio.wait(
            (
                asyncio.create_task(pub_broker.publish("hello", queue)),
                asyncio.create_task(event.wait()),
            ),
            timeout=3,
        )

        assert event.is_set()
        subscriber.mock.assert_called_with("hello")

    async def test_manual_publisher_mock(
        self, router: BrokerRouter, queue: str, pub_broker: BrokerAsyncUsecase
    ):
        publisher = router.publisher(queue + "resp")

        @pub_broker.subscriber(queue)
        async def m(m):
            await publisher.publish("response")

        pub_broker.include_router(router)
        await pub_broker.start()
        await pub_broker.publish("hello", queue)
        publisher.mock.assert_called_with("response")
