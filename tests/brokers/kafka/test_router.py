import pytest

from propan.kafka import KafkaRoute, KafkaRouter
from tests.brokers.base.router import RouterLocalTestcase, RouterTestcase


@pytest.mark.kafka
class TestRouter(RouterTestcase):
    broker_class = KafkaRouter
    route_class = KafkaRoute


class TestRabbitRouterLocal(RouterLocalTestcase):
    broker_class = KafkaRouter
    route_class = KafkaRoute
