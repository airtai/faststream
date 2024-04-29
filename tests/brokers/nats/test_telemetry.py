import pytest

from faststream.broker.core.usecase import BrokerUsecase
from faststream.nats import NatsBroker
from faststream.opentelemetry import TelemetryMiddleware
from tests.brokers.base.telemetry import LocalTelemetryTestcase

from .test_consume import TestConsume
from .test_publish import TestPublish


@pytest.mark.nats()
class TestTelemetry(LocalTelemetryTestcase):
    messaging_system = "nats"
    broker_class = NatsBroker


@pytest.mark.nats()
class TestPublishWithTelemetry(TestPublish):
    @pytest.fixture()
    def pub_broker(self, full_broker):
        full_broker._middlewares = (*full_broker._middlewares, TelemetryMiddleware())
        return full_broker


@pytest.mark.nats()
class TestConsumeWithTelemetry(TestConsume):
    @pytest.fixture()
    def consume_broker(self, broker: BrokerUsecase):
        broker._middlewares = (*broker._middlewares, TelemetryMiddleware())
        return broker
