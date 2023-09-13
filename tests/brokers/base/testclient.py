import pytest

from faststream.broker.core.abc import BrokerUsecase
from faststream.types import AnyCallable
from tests.brokers.base.consume import BrokerConsumeTestcase
from tests.brokers.base.publish import BrokerPublishTestcase
from tests.brokers.base.rpc import BrokerRPCTestcase


class BrokerTestclientTestcase(
    BrokerPublishTestcase, BrokerConsumeTestcase, BrokerRPCTestcase
):
    build_message: AnyCallable

    @pytest.fixture
    def pub_broker(self, test_broker):
        yield test_broker

    @pytest.fixture
    def consume_broker(self, test_broker):
        yield test_broker

    @pytest.fixture
    def rpc_broker(self, test_broker):
        yield test_broker

    @pytest.mark.asyncio
    async def test_subscriber_mock(self, queue: str, test_broker: BrokerUsecase):
        @test_broker.subscriber(queue)
        async def m():
            pass

        await test_broker.start()
        await test_broker.publish("hello", queue)
        m.mock.assert_called_once_with("hello")

    @pytest.mark.asyncio
    async def test_publisher_mock(self, queue: str, test_broker: BrokerUsecase):
        publisher = test_broker.publisher(queue + "resp")

        @publisher
        @test_broker.subscriber(queue)
        async def m():
            return "response"

        await test_broker.start()
        await test_broker.publish("hello", queue)
        publisher.mock.assert_called_with("response")

    @pytest.mark.asyncio
    async def test_manual_publisher_mock(self, queue: str, test_broker: BrokerUsecase):
        publisher = test_broker.publisher(queue + "resp")

        @test_broker.subscriber(queue)
        async def m():
            await publisher.publish("response")

        await test_broker.start()
        await test_broker.publish("hello", queue)
        publisher.mock.assert_called_with("response")

    @pytest.mark.asyncio
    async def test_exception_raises(self, queue: str, test_broker: BrokerUsecase):
        @test_broker.subscriber(queue)
        async def m():  # pragma: no cover
            raise ValueError()

        await test_broker.start()

        with pytest.raises(ValueError):
            await test_broker.publish("hello", queue)
