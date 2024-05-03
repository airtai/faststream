import pytest

from faststream.broker.core.usecase import BrokerUsecase
from faststream.redis import RedisBroker
from faststream.redis.opentelemetry import RedisTelemetryMiddleware
from tests.brokers.redis.test_consume import (
    TestConsume,
    TestConsumeList,
    TestConsumeStream,
)
from tests.brokers.redis.test_publish import TestPublish

from ..basic import LocalTelemetryTestcase


@pytest.mark.redis()
class TestTelemetry(LocalTelemetryTestcase):
    messaging_system = "redis"
    broker_class = RedisBroker
    telemetry_middleware_class = RedisTelemetryMiddleware


@pytest.mark.redis()
class TestPublishWithTelemetry(TestPublish):
    @pytest.fixture()
    def pub_broker(self):
        return RedisBroker(middlewares=(RedisTelemetryMiddleware(),))


@pytest.mark.redis()
class TestConsumeWithTelemetry(TestConsume):
    @pytest.fixture()
    def consume_broker(self):
        return RedisBroker(middlewares=(RedisTelemetryMiddleware(),))

@pytest.mark.redis()
class TestConsumeListWithTelemetry(TestConsumeList):
    @pytest.fixture()
    def consume_broker(self):
        return RedisBroker(middlewares=(RedisTelemetryMiddleware(),))


@pytest.mark.redis()
class TestConsumeStreamWithTelemetry(TestConsumeStream):
    @pytest.fixture()
    def consume_broker(self):
        return RedisBroker(middlewares=(RedisTelemetryMiddleware(),))
