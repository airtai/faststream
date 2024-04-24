import pytest

from faststream.nats import NatsBroker
from tests.brokers.base.telemetry import LocalTelemetryTestcase


@pytest.mark.nats()
class TestMiddlewares(LocalTelemetryTestcase):
    messaging_system = "nats"
    broker_class = NatsBroker
