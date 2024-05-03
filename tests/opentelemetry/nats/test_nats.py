import pytest

from faststream.nats import JStream, NatsBroker
from faststream.nats.opentelemetry import NatsTelemetryMiddleware
from tests.brokers.nats.test_consume import TestConsume
from tests.brokers.nats.test_publish import TestPublish

from ..basic import LocalTelemetryTestcase


@pytest.fixture()
def stream(queue):
    return JStream(queue)


@pytest.mark.nats()
class TestTelemetry(LocalTelemetryTestcase):
    messaging_system = "nats"
    broker_class = NatsBroker
    telemetry_middleware_class = NatsTelemetryMiddleware


@pytest.mark.nats()
class TestPublishWithTelemetry(TestPublish):
    def get_broker(self):
        return NatsBroker(
            middlewares=(NatsTelemetryMiddleware(),),
        )


@pytest.mark.nats()
class TestConsumeWithTelemetry(TestConsume):
    def get_broker(self, apply_types: bool = False):
        return NatsBroker(
            middlewares=(NatsTelemetryMiddleware(),),
            apply_types=apply_types,
        )
