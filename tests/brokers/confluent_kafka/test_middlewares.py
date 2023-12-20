import pytest

from faststream.kafka import ConfluentKafkaBroker
from tests.brokers.base.middlewares import MiddlewareTestcase


@pytest.mark.confluent
class TestMiddlewares(MiddlewareTestcase):
    broker_class = ConfluentKafkaBroker
