import pytest

from faststream.confluent import KafkaPublisher, KafkaRoute, KafkaRouter
from tests.brokers.base.router import RouterLocalTestcase, RouterTestcase

from .basic import ConfluentTestcaseConfig


@pytest.mark.confluent
class TestRouter(ConfluentTestcaseConfig, RouterTestcase):
    broker_class = KafkaRouter
    route_class = KafkaRoute
    publisher_class = KafkaPublisher


class TestRouterLocal(ConfluentTestcaseConfig, RouterLocalTestcase):
    broker_class = KafkaRouter
    route_class = KafkaRoute
    publisher_class = KafkaPublisher
