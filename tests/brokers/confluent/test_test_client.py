import asyncio

import pytest

from faststream import BaseMiddleware
from faststream.confluent import KafkaBroker, TestKafkaBroker
from tests.brokers.base.testclient import BrokerTestclientTestcase


@pytest.mark.asyncio()
class TestTestclient(BrokerTestclientTestcase):
    """A class to represent a test Kafka broker."""

    @pytest.mark.confluent()
    async def test_with_real_testclient(
        self,
        broker: KafkaBroker,
        queue: str,
        event: asyncio.Event,
    ):
        @broker.subscriber(queue, auto_offset_reset="earliest")
        def subscriber(m):
            event.set()

        async with TestKafkaBroker(broker, with_real=True) as br:
            await asyncio.wait(
                (
                    asyncio.create_task(br.publish("hello", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=10,
            )

        assert event.is_set()

    async def test_batch_pub_by_default_pub(
        self,
        test_broker: KafkaBroker,
        queue: str,
    ):
        @test_broker.subscriber(queue, batch=True, auto_offset_reset="earliest")
        async def m():
            pass

        await test_broker.start()
        await test_broker.publish("hello", queue)
        m.mock.assert_called_once_with(["hello"])

    async def test_batch_pub_by_pub_batch(
        self,
        test_broker: KafkaBroker,
        queue: str,
    ):
        @test_broker.subscriber(queue, batch=True, auto_offset_reset="earliest")
        async def m():
            pass

        await test_broker.start()
        await test_broker.publish_batch("hello", topic=queue)
        m.mock.assert_called_once_with(["hello"])

    async def test_batch_publisher_mock(
        self,
        test_broker: KafkaBroker,
        queue: str,
    ):
        publisher = test_broker.publisher(queue + "1", batch=True)

        @publisher
        @test_broker.subscriber(queue, auto_offset_reset="earliest")
        async def m():
            return 1, 2, 3

        await test_broker.start()
        await test_broker.publish("hello", queue)
        m.mock.assert_called_once_with("hello")
        publisher.mock.assert_called_once_with([1, 2, 3])

    async def test_respect_middleware(self, queue):
        routes = []

        class Middleware(BaseMiddleware):
            async def on_receive(self) -> None:
                routes.append(None)
                return await super().on_receive()

        broker = KafkaBroker(middlewares=(Middleware,))

        @broker.subscriber(queue, auto_offset_reset="earliest")
        async def h1(): ...

        @broker.subscriber(queue + "1", auto_offset_reset="earliest")
        async def h2(): ...

        async with TestKafkaBroker(broker) as br:
            await br.publish("", queue)
            await br.publish("", queue + "1")

        assert len(routes) == 2

    @pytest.mark.confluent()
    async def test_real_respect_middleware(self, queue):
        routes = []

        class Middleware(BaseMiddleware):
            async def on_receive(self) -> None:
                routes.append(None)
                return await super().on_receive()

        broker = KafkaBroker(middlewares=(Middleware,))

        @broker.subscriber(queue, auto_offset_reset="earliest")
        async def h1(): ...

        @broker.subscriber(queue + "1", auto_offset_reset="earliest")
        async def h2(): ...

        async with TestKafkaBroker(broker, with_real=True) as br:
            await br.publish("", queue)
            await br.publish("", queue + "1")
            await h1.wait_call(10)
            await h2.wait_call(10)

        assert len(routes) == 2

    @pytest.mark.confluent()
    async def test_multiple_subscribers_with_different_groups(
        self,
        queue: str,
        test_broker: KafkaBroker,
    ):
        @test_broker.subscriber(queue, group_id="group1")
        async def subscriber1(): ...

        @test_broker.subscriber(queue, group_id="group2")
        async def subscriber2(): ...

        await test_broker.start()
        await test_broker.publish("", queue)

        assert subscriber1.mock.call_count == 1
        assert subscriber2.mock.call_count == 1

    @pytest.mark.confluent()
    async def test_multiple_subscribers_with_same_group(
        self,
        queue: str,
        test_broker: KafkaBroker,
    ):
        @test_broker.subscriber(queue, group_id="group1")
        async def subscriber1(): ...

        @test_broker.subscriber(queue, group_id="group1")
        async def subscriber2(): ...

        await test_broker.start()
        await test_broker.publish("", queue)

        assert subscriber1.mock.call_count == 1
        assert subscriber2.mock.call_count == 0

    async def test_multiple_batch_subscriber_with_different_group(
        self,
        test_broker: KafkaBroker,
        queue: str,
    ):
        @test_broker.subscriber(queue, batch=True, group_id="group1")
        async def subscriber1(): ...

        @test_broker.subscriber(queue, batch=True, group_id="group2")
        async def subscriber2(): ...

        await test_broker.start()
        await test_broker.publish("", queue)

        assert subscriber1.mock.call_count == 1
        assert subscriber2.mock.call_count == 1

    async def test_multiple_batch_subscriber_with_same_group(
        self,
        test_broker: KafkaBroker,
        queue: str,
    ):
        @test_broker.subscriber(queue, batch=True, group_id="group1")
        async def subscriber1(): ...

        @test_broker.subscriber(queue, batch=True, group_id="group1")
        async def subscriber2(): ...

        await test_broker.start()
        await test_broker.publish("", queue)

        assert subscriber1.mock.call_count == 1
        assert subscriber2.mock.call_count == 0
