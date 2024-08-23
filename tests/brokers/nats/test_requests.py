import pytest

from faststream.nats import NatsBroker, NatsRouter, TestNatsBroker
from tests.brokers.base.requests import RequestsTestcase


@pytest.mark.asyncio
class NatsRequestsTestcase(RequestsTestcase):
    def get_broker(self, **kwargs):
        return NatsBroker(**kwargs)

    def get_router(self, **kwargs):
        return NatsRouter(**kwargs)

    async def test_broker_stream_request(self, queue: str):
        broker = self.get_broker()

        stream_name = f"{queue}st"

        args, kwargs = self.get_subscriber_params(queue, stream=stream_name)

        @broker.subscriber(*args, **kwargs)
        async def handler(msg):
            return "Response"

        async with self.patch_broker(broker):
            await broker.start()

            response = await broker.request(
                None,
                queue,
                correlation_id="1",
                stream=stream_name,
                timeout=self.timeout,
            )

        assert await response.decode() == "Response"
        assert response.correlation_id == "1"

    async def test_publisher_stream_request(self, queue: str):
        broker = self.get_broker()

        stream_name = f"{queue}st"
        publisher = broker.publisher(queue, stream=stream_name)

        args, kwargs = self.get_subscriber_params(queue, stream=stream_name)

        @broker.subscriber(*args, **kwargs)
        async def handler(msg):
            return "Response"

        async with self.patch_broker(broker):
            await broker.start()

            response = await publisher.request(
                None,
                correlation_id="1",
                timeout=self.timeout,
            )

        assert await response.decode() == "Response"
        assert response.correlation_id == "1"


@pytest.mark.nats
class TestRealRequests(NatsRequestsTestcase):
    pass


class TestRequestTestClient(NatsRequestsTestcase):
    def patch_broker(self, broker, **kwargs):
        return TestNatsBroker(broker, **kwargs)
