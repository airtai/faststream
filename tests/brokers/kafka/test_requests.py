import pytest

from faststream.kafka import KafkaBroker, KafkaRouter, TestKafkaBroker
from tests.brokers.base.requests import RequestsTestcase


@pytest.mark.asyncio
class TestRequestTestClient(RequestsTestcase):
    def get_broker(self):
        return KafkaBroker()

    def get_router(self):
        return KafkaRouter()

    def patch_broker(self, broker):
        return TestKafkaBroker(broker)
