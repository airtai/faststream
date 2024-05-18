import pytest

from faststream.testing.broker import TestBroker
from faststream.types import AnyCallable
from tests.brokers.base.consume import BrokerConsumeTestcase
from tests.brokers.base.publish import BrokerPublishTestcase
from tests.brokers.base.rpc import BrokerRPCTestcase


class BrokerTestclientTestcase(
    BrokerPublishTestcase,
    BrokerConsumeTestcase,
    BrokerRPCTestcase,
):
    build_message: AnyCallable
    test_class: TestBroker

    @pytest.mark.asyncio()
    async def test_subscriber_mock(self, queue: str):
        test_broker = self.get_broker()

        @test_broker.subscriber(queue)
        async def m(msg):
            pass

        async with self.test_class(test_broker):
            await test_broker.start()
            await test_broker.publish("hello", queue)
            m.mock.assert_called_once_with("hello")

    @pytest.mark.asyncio()
    async def test_publisher_mock(self, queue: str):
        test_broker = self.get_broker()

        publisher = test_broker.publisher(queue + "resp")

        @publisher
        @test_broker.subscriber(queue)
        async def m(msg):
            return "response"

        async with self.test_class(test_broker):
            await test_broker.start()
            await test_broker.publish("hello", queue)
            publisher.mock.assert_called_with("response")

    @pytest.mark.asyncio()
    async def test_manual_publisher_mock(self, queue: str):
        test_broker = self.get_broker()

        publisher = test_broker.publisher(queue + "resp")

        @test_broker.subscriber(queue)
        async def m(msg):
            await publisher.publish("response")

        async with self.test_class(test_broker):
            await test_broker.start()
            await test_broker.publish("hello", queue)
            publisher.mock.assert_called_with("response")

    @pytest.mark.asyncio()
    async def test_exception_raises(self, queue: str):
        test_broker = self.get_broker()

        @test_broker.subscriber(queue)
        async def m(msg):  # pragma: no cover
            raise ValueError()

        async with self.test_class(test_broker):
            await test_broker.start()

            with pytest.raises(ValueError):  # noqa: PT011
                await test_broker.publish("hello", queue)
