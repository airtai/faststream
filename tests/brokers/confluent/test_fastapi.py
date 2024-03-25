import pytest

from faststream.kafka.fastapi import KafkaRouter
from faststream.kafka.test import TestKafkaBroker, build_message
from tests.brokers.base.fastapi import FastAPILocalTestcase, FastAPITestcase


@pytest.mark.confluent()
class TestRabbitRouter(FastAPITestcase):
    """A class to represent a test Kafka broker."""

    router_class = KafkaRouter


class TestRouterLocal(FastAPILocalTestcase):
    """A class to represent a test Kafka broker."""

    router_class = KafkaRouter
    broker_test = staticmethod(TestKafkaBroker)
    build_message = staticmethod(build_message)
