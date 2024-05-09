import asyncio

import pytest

from faststream import BaseMiddleware
from faststream.kafka import KafkaBroker, TestKafkaBroker, TopicPartition
from tests.brokers.base.testclient import BrokerTestclientTestcase


@pytest.mark.asyncio()
class TestTestclient(BrokerTestclientTestcase):
    test_class = TestKafkaBroker

    def get_broker(self, apply_types: bool = False):
        return KafkaBroker(apply_types=apply_types)

    def patch_broker(self, broker: KafkaBroker) -> TestKafkaBroker:
        return TestKafkaBroker(broker)

    async def test_partition_match(
        self,
        queue: str,
    ):
        broker = self.get_broker()
      
        @broker.subscriber(partitions=[TopicPartition(queue, 1)])
        async def m():
            pass

        async with self.patch_broker(broker) as br:
            await  br.publish("hello", queue)

            m.mock.assert_called_once_with("hello")

    async def test_partition_match_exect(
        self,
        queue: str,
    ):
        broker = self.get_broker()
      
        @broker.subscriber(partitions=[TopicPartition(queue, 1)])
        async def m():
            pass

        async with self.patch_broker(broker) as br:
            await test_broker.publish("hello", queue, partition=1)

            m.mock.assert_called_once_with("hello")

    async def test_partition_missmatch(
        self,
        queue: str,
    ):
        broker = self.get_broker()

        @broker.subscriber(partitions=[TopicPartition(queue, 1)])
        async def m():
            pass

        @broker.subscriber(queue)
        async def m2():
            pass
        
        async with self.patch_broker(broker) as br:
            await br.publish("hello", queue, partition=2)

            assert not m.mock.called
            m2.mock.assert_called_once_with("hello")

    @pytest.mark.kafka()
    async def test_with_real_testclient(
        self,
        queue: str,
        event: asyncio.Event,
    ):
        broker = self.get_broker()

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
        queue: str,
    ):
        broker = self.get_broker()

        @broker.subscriber(queue, batch=True)
        async def m(msg):
            pass

        async with TestKafkaBroker(broker) as br:
            await br.publish("hello", queue)
            m.mock.assert_called_once_with(["hello"])

    async def test_batch_pub_by_pub_batch(
        self,
        queue: str,
    ):
        broker = self.get_broker()

        @broker.subscriber(queue, batch=True)
        async def m(msg):
            pass

        async with TestKafkaBroker(broker) as br:
            await br.publish_batch("hello", topic=queue)
            m.mock.assert_called_once_with(["hello"])

    async def test_batch_publisher_mock(
        self,
        queue: str,
    ):
        broker = self.get_broker()

        publisher = broker.publisher(queue + "1", batch=True)

        @publisher
        @broker.subscriber(queue)
        async def m(msg):
            return 1, 2, 3

        async with TestKafkaBroker(broker) as br:
            await br.publish("hello", queue)
            m.mock.assert_called_once_with("hello")
            publisher.mock.assert_called_once_with([1, 2, 3])

    async def test_respect_middleware(self, queue):
        routes = []

        class Middleware(BaseMiddleware):
            async def on_receive(self) -> None:
                routes.append(None)
                return await super().on_receive()

        broker = KafkaBroker(middlewares=(Middleware,))

        @broker.subscriber(queue)
        async def h1(): ...

        @broker.subscriber(queue + "1")
        async def h2(): ...

        async with TestKafkaBroker(broker) as br:
            await br.publish("", queue)
            await br.publish("", queue + "1")

        assert len(routes) == 2

    @pytest.mark.kafka()
    async def test_real_respect_middleware(self, queue):
        routes = []

        class Middleware(BaseMiddleware):
            async def on_receive(self) -> None:
                routes.append(None)
                return await super().on_receive()

        broker = KafkaBroker(middlewares=(Middleware,))

        @broker.subscriber(queue)
        async def h1(): ...

        @broker.subscriber(queue + "1")
        async def h2(): ...

        async with TestKafkaBroker(broker, with_real=True) as br:
            await br.publish("", queue)
            await br.publish("", queue + "1")
            await h1.wait_call(3)
            await h2.wait_call(3)

        assert len(routes) == 2
