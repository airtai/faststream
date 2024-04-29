import pytest

from faststream.broker.core.usecase import BrokerUsecase
from faststream.opentelemetry import TelemetryMiddleware
from faststream.redis import RedisBroker
from tests.brokers.base.telemetry import LocalTelemetryTestcase

from .test_consume import TestConsume
from .test_publish import TestPublish


@pytest.mark.redis()
class TestTelemetry(LocalTelemetryTestcase):
    messaging_system = "redis"
    broker_class = RedisBroker


@pytest.mark.redis()
class TestPublishWithTelemetry(TestPublish):
    @pytest.fixture()
    def pub_broker(self, full_broker):
        full_broker._middlewares = (*full_broker._middlewares, TelemetryMiddleware())
        return full_broker


@pytest.mark.redis()
class TestConsumeWithTelemetry(TestConsume):
    @pytest.fixture()
    def consume_broker(self, broker: BrokerUsecase):
        broker._middlewares = (*broker._middlewares, TelemetryMiddleware())
        return broker
