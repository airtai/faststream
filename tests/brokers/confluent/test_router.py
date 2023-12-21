import pytest

from faststream.kafka import KafkaRoute, KafkaRouter
from tests.brokers.base.router import RouterLocalTestcase, RouterTestcase


@pytest.mark.confluent()
class TestRouter(RouterTestcase):
    """A class to represent a test Kafka broker."""

    broker_class = KafkaRouter
    route_class = KafkaRoute


class TestRouterLocal(RouterLocalTestcase):
    """A class to represent a test Kafka broker."""

    broker_class = KafkaRouter
    route_class = KafkaRoute
