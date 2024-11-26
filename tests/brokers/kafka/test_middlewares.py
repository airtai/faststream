import pytest

from faststream.kafka import KafkaBroker
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


@pytest.mark.kafka
class TestMiddlewaresOrder(MiddlewaresOrderTestcase):
    broker_class = KafkaBroker
