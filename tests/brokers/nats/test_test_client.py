import asyncio

import pytest

from faststream.nats import JsStream, NatsBroker, TestNatsBroker
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

    @pytest.mark.asyncio
    async def test_js_subscriber_mock(
        self, queue: str, test_broker: NatsBroker, stream: JsStream
    ):
        @test_broker.subscriber(queue, stream=stream)
        async def m():
            pass

        await test_broker.start()
        await test_broker.publish("hello", queue, stream=stream.name)
        m.mock.assert_called_once_with("hello")

    @pytest.mark.asyncio
    async def test_js_publisher_mock(
        self, queue: str, test_broker: NatsBroker, stream: JsStream
    ):
        publisher = test_broker.publisher(queue + "resp")

        @publisher
        @test_broker.subscriber(queue, stream=stream)
        async def m():
            return "response"

        await test_broker.start()
        await test_broker.publish("hello", queue, stream=stream.name)
        publisher.mock.assert_called_with("response")

    @pytest.mark.asyncio
    async def test_any_subject_routing(self, test_broker: NatsBroker):
        @test_broker.subscriber("test.*.subj.*")
        def subscriber():
            ...

        await test_broker.start()
        await test_broker.publish("hello", "test.a.subj.b")
        subscriber.mock.assert_called_once_with("hello")

    @pytest.mark.asyncio
    async def test_ending_subject_routing(self, test_broker: NatsBroker):
        @test_broker.subscriber("test.>")
        def subscriber():
            ...

        await test_broker.start()
        await test_broker.publish("hello", "test.a.subj.b")
        subscriber.mock.assert_called_once_with("hello")

    @pytest.mark.asyncio
    async def test_mixed_subject_routing(self, test_broker: NatsBroker):
        @test_broker.subscriber("*.*.subj.>")
        def subscriber():
            ...

        await test_broker.start()
        await test_broker.publish("hello", "test.a.subj.b.c")
        subscriber.mock.assert_called_once_with("hello")
