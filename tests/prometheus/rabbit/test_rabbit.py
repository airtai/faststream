import pytest
from prometheus_client import CollectorRegistry

from faststream.rabbit import RabbitBroker, RabbitExchange
from faststream.rabbit.prometheus.middleware import RabbitPrometheusMiddleware
from tests.brokers.rabbit.test_consume import TestConsume
from tests.brokers.rabbit.test_publish import TestPublish
from tests.prometheus.basic import LocalPrometheusTestcase


@pytest.fixture
def exchange(queue):
    return RabbitExchange(name=queue)


@pytest.mark.rabbit
class TestPrometheus(LocalPrometheusTestcase):
    def get_broker(self, **kwargs):
        return RabbitBroker(**kwargs)

    def get_middleware(self, **kwargs):
        return RabbitPrometheusMiddleware(**kwargs)


@pytest.mark.rabbit
class TestPublishWithPrometheus(TestPublish):
    def get_broker(self, apply_types: bool = False):
        return RabbitBroker(
            middlewares=(RabbitPrometheusMiddleware(registry=CollectorRegistry()),),
            apply_types=apply_types,
        )


@pytest.mark.rabbit
class TestConsumeWithPrometheus(TestConsume):
    def get_broker(self, apply_types: bool = False):
        return RabbitBroker(
            middlewares=(RabbitPrometheusMiddleware(registry=CollectorRegistry()),),
            apply_types=apply_types,
        )
