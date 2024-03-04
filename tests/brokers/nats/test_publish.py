import pytest

from tests.brokers.base.publish import BrokerPublishTestcase


@pytest.mark.nats()
class TestPublish(BrokerPublishTestcase):
    """Test publish method of NATS broker."""

    @pytest.mark.asyncio()
    async def test_stream_publish(
        self,
        queue: str,
        test_broker,
    ):
        @test_broker.subscriber(queue, stream="test")
        async def m(): ...

        await test_broker.start()
        await test_broker.publish("Hi!", queue, stream="test")
        m.mock.assert_called_once_with("Hi!")

    @pytest.mark.asyncio()
    async def test_wrong_stream_publish(
        self,
        queue: str,
        test_broker,
    ):
        @test_broker.subscriber(queue)
        async def m(): ...

        await test_broker.start()
        await test_broker.publish("Hi!", queue, stream="test")
        assert not m.mock.called
