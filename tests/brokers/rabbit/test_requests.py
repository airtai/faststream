import pytest

from faststream.rabbit import RabbitBroker, RabbitRouter, TestRabbitBroker
from tests.brokers.base.requests import RequestsTestcase


@pytest.mark.asyncio
class RabbitRequestsTestcase(RequestsTestcase):
    def get_broker(self, **kwargs):
        return RabbitBroker(**kwargs)

    def get_router(self, **kwargs):
        return RabbitRouter(**kwargs)


@pytest.mark.rabbit
class TestRealRequests(RabbitRequestsTestcase):
    pass


@pytest.mark.asyncio
class TestRequestTestClient(RabbitRequestsTestcase):
    def patch_broker(self, broker, **kwargs):
        return TestRabbitBroker(broker, **kwargs)
