import pytest
from prometheus_client import CollectorRegistry

from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitMessage
from faststream.rabbit.prometheus.middleware import RabbitPrometheusMiddleware
from tests.brokers.rabbit.test_consume import TestConsume
from tests.brokers.rabbit.test_publish import TestPublish
from tests.prometheus.basic import LocalPrometheusTestcase


@pytest.fixture
def exchange(queue):
    return RabbitExchange(name=queue)


@pytest.mark.rabbit
class TestPrometheus(LocalPrometheusTestcase):
    broker_class = RabbitBroker
    middleware_class = RabbitPrometheusMiddleware
    message_class = RabbitMessage


@pytest.mark.rabbit
class TestPublishWithPrometheus(TestPublish):
    def get_broker(self, apply_types: bool = False):
        return RabbitBroker(
            middlewares=(RabbitPrometheusMiddleware(registry=CollectorRegistry()),),
            apply_types=apply_types,
        )


@pytest.mark.rabbit
class TestConsumeWithTelemetry(TestConsume):
    def get_broker(self, apply_types: bool = False):
        return RabbitBroker(
            middlewares=(RabbitPrometheusMiddleware(registry=CollectorRegistry()),),
            apply_types=apply_types,
        )
