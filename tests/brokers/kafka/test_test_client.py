import asyncio

import pytest

from faststream.kafka import KafkaBroker, TestKafkaBroker
from tests.brokers.base.testclient import BrokerTestclientTestcase


@pytest.mark.asyncio
class TestTestclient(BrokerTestclientTestcase):
    @pytest.mark.kafka
    async def test_with_real_testclient(
        self,
        broker: KafkaBroker,
        queue: str,
        event: asyncio.Event,
    ):
        @broker.subscriber(queue)
        def subscriber(m):
            event.set()

        async with TestKafkaBroker(broker, with_real=True) as br:
            await asyncio.wait(
                (
                    asyncio.create_task(br.publish("hello", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        assert event.is_set()

    async def test_batch_pub_by_default_pub(
        self,
        test_broker: KafkaBroker,
        queue: str,
    ):
        @test_broker.subscriber(queue, batch=True)
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
        @test_broker.subscriber(queue, batch=True)
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
        @test_broker.subscriber(queue)
        async def m():
            return 1, 2, 3

        await test_broker.start()
        await test_broker.publish("hello", queue)
        m.mock.assert_called_once_with("hello")
        publisher.mock.assert_called_once_with([1, 2, 3])
