import asyncio

import pytest

from faststream import BaseMiddleware
from faststream.nats import JStream, NatsBroker, PullSub, TestNatsBroker
from tests.brokers.base.testclient import BrokerTestclientTestcase


@pytest.mark.asyncio
class TestTestclient(BrokerTestclientTestcase):
    @pytest.mark.nats
    async def test_with_real_testclient(
        self,
        broker: NatsBroker,
        queue: str,
        event: asyncio.Event,
    ):
        @broker.subscriber(queue)
        def subscriber(m):
            event.set()

        async with TestNatsBroker(broker, with_real=True) as br:
            await asyncio.wait(
                (
                    asyncio.create_task(br.publish("hello", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        assert event.is_set()

    async def test_respect_middleware(self, queue):
        routes = []

        class Middleware(BaseMiddleware):
            async def on_receive(self) -> None:
                routes.append(None)
                return await super().on_receive()

        broker = NatsBroker()
        broker.middlewares = (Middleware,)

        @broker.subscriber(queue)
        async def h1():
            ...

        @broker.subscriber(queue + "1")
        async def h2():
            ...

        async with TestNatsBroker(broker) as br:
            await br.publish("", queue)
            await br.publish("", queue + "1")

        assert len(routes) == 2

    @pytest.mark.nats
    async def test_real_respect_middleware(self, queue):
        routes = []

        class Middleware(BaseMiddleware):
            async def on_receive(self) -> None:
                routes.append(None)
                return await super().on_receive()

        broker = NatsBroker()
        broker.middlewares = (Middleware,)

        @broker.subscriber(queue)
        async def h1():
            ...

        @broker.subscriber(queue + "1")
        async def h2():
            ...

        async with TestNatsBroker(broker, with_real=True) as br:
            await br.publish("", queue)
            await br.publish("", queue + "1")
            await h1.wait_call(3)
            await h2.wait_call(3)

        assert len(routes) == 2

    async def test_js_subscriber_mock(
        self, queue: str, test_broker: NatsBroker, stream: JStream
    ):
        @test_broker.subscriber(queue, stream=stream)
        async def m():
            pass

        await test_broker.start()
        await test_broker.publish("hello", queue, stream=stream.name)
        m.mock.assert_called_once_with("hello")

    async def test_js_publisher_mock(
        self, queue: str, test_broker: NatsBroker, stream: JStream
    ):
        publisher = test_broker.publisher(queue + "resp")

        @publisher
        @test_broker.subscriber(queue, stream=stream)
        async def m():
            return "response"

        await test_broker.start()
        await test_broker.publish("hello", queue, stream=stream.name)
        publisher.mock.assert_called_with("response")

    async def test_any_subject_routing(self, test_broker: NatsBroker):
        @test_broker.subscriber("test.*.subj.*")
        def subscriber():
            ...

        await test_broker.start()
        await test_broker.publish("hello", "test.a.subj.b")
        subscriber.mock.assert_called_once_with("hello")

    async def test_ending_subject_routing(self, test_broker: NatsBroker):
        @test_broker.subscriber("test.>")
        def subscriber():
            ...

        await test_broker.start()
        await test_broker.publish("hello", "test.a.subj.b")
        subscriber.mock.assert_called_once_with("hello")

    async def test_mixed_subject_routing(self, test_broker: NatsBroker):
        @test_broker.subscriber("*.*.subj.>")
        def subscriber():
            ...

        await test_broker.start()
        await test_broker.publish("hello", "test.a.subj.b.c")
        subscriber.mock.assert_called_once_with("hello")

    async def test_consume_pull(
        self,
        queue: str,
        test_broker: NatsBroker,
        stream: JStream,
    ):
        @test_broker.subscriber(queue, stream=stream, pull_sub=PullSub(1))
        def subscriber(m):
            ...

        await test_broker.start()
        await test_broker.publish("hello", queue)
        subscriber.mock.assert_called_once_with("hello")
