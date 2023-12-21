import pytest

from faststream.kafka import KafkaBroker
from tests.brokers.base.middlewares import MiddlewareTestcase


@pytest.mark.kafka()
class TestMiddlewares(MiddlewareTestcase):  # noqa: D101
    broker_class = KafkaBroker
