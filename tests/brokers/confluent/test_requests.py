import pytest

from faststream.confluent import KafkaBroker, KafkaRouter, TestKafkaBroker
from tests.brokers.base.requests import RequestsTestcase

from .basic import ConfluentTestcaseConfig


@pytest.mark.asyncio
class TestRequestTestClient(ConfluentTestcaseConfig, RequestsTestcase):
    def get_broker(self, **kwargs):
        return KafkaBroker(**kwargs)

    def get_router(self, **kwargs):
        return KafkaRouter(**kwargs)

    def patch_broker(self, broker, **kwargs):
        return TestKafkaBroker(broker, **kwargs)
