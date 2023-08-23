import pytest

from propan.kafka import KafkaBroker
from tests.brokers.base.middlewares import MiddlewareTestcase


@pytest.mark.kafka
class TestMiddlewares(MiddlewareTestcase):
    broker_class = KafkaBroker
