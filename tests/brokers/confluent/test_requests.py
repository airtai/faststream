import pytest

from faststream.confluent import KafkaBroker, KafkaRouter, TestKafkaBroker
from tests.brokers.base.requests import RequestsTestcase

from .basic import ConfluentTestcaseConfig


@pytest.mark.asyncio
class TestRequestTestClient(ConfluentTestcaseConfig, RequestsTestcase):
    def get_broker(self):
        return KafkaBroker()

    def get_router(self):
        return KafkaRouter()

    def patch_broker(self, broker):
        return TestKafkaBroker(broker)
