import pytest

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
    def get_broker(self, apply_types: bool = False):
        return RedisBroker(
            middlewares=(RedisTelemetryMiddleware(),),
            apply_types=apply_types,
        )


@pytest.mark.redis()
class TestConsumeWithTelemetry(TestConsume):
    def get_broker(self, apply_types: bool = False):
        return RedisBroker(
            middlewares=(RedisTelemetryMiddleware(),),
            apply_types=apply_types,
        )


@pytest.mark.redis()
class TestConsumeListWithTelemetry(TestConsumeList):
    def get_broker(self, apply_types: bool = False):
        return RedisBroker(
            middlewares=(RedisTelemetryMiddleware(),),
            apply_types=apply_types,
        )


@pytest.mark.redis()
class TestConsumeStreamWithTelemetry(TestConsumeStream):
    def get_broker(self, apply_types: bool = False):
        return RedisBroker(
            middlewares=(RedisTelemetryMiddleware(),),
            apply_types=apply_types,
        )
