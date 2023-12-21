import pytest

from faststream.kafka import ConfluentKafkaBroker
from tests.brokers.base.middlewares import MiddlewareTestcase


@pytest.mark.confluent()
class TestMiddlewares(MiddlewareTestcase):
    """A class to represent a test Kafka broker."""

    broker_class = ConfluentKafkaBroker
