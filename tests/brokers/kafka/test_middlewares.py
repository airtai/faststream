import pytest

from faststream.kafka import KafkaBroker, TestKafkaBroker
from tests.brokers.base.middlewares import (
    ExceptionMiddlewareTestcase,
    MiddlewareTestcase,
    MiddlewaresOrderTestcase,
)


@pytest.mark.kafka
class TestMiddlewares(MiddlewareTestcase):
    broker_class = KafkaBroker


@pytest.mark.kafka
class TestExceptionMiddlewares(ExceptionMiddlewareTestcase):
    broker_class = KafkaBroker


class TestMiddlewaresOrder(MiddlewaresOrderTestcase):
    broker_class = KafkaBroker

    def patch_broker(self, broker: KafkaBroker) -> TestKafkaBroker:
        return TestKafkaBroker(broker)
