import pytest

from faststream.kafka import ConfluentKafkaBroker
from tests.brokers.base.middlewares import MiddlewareTestcase


@pytest.mark.confluent_kafka
class TestMiddlewares(MiddlewareTestcase):
    broker_class = ConfluentKafkaBroker
