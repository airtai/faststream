import pytest

from faststream.redis import RedisBroker
from tests.brokers.base.telemetry import LocalTelemetryTestcase


@pytest.mark.redis()
class TestTelemetry(LocalTelemetryTestcase):
    messaging_system = "redis"
    broker_class = RedisBroker
