import pytest

from faststream.rabbit import RabbitBroker, RabbitRouter, TestRabbitBroker
from tests.brokers.base.requests import RequestsTestcase


@pytest.mark.asyncio
class RabbitRequestsTestcase(RequestsTestcase):
    def get_broker(self):
        return RabbitBroker()

    def get_router(self):
        return RabbitRouter()


@pytest.mark.rabbit
class TestRealRequests(RabbitRequestsTestcase):
    pass


@pytest.mark.asyncio
class TestRequestTestClient(RabbitRequestsTestcase):
    def patch_broker(self, broker):
        return TestRabbitBroker(broker)
