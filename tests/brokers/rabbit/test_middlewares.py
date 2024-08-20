import pytest

from faststream.rabbit import RabbitBroker
from tests.brokers.base.middlewares import (
    ExceptionMiddlewareTestcase,
    MiddlewareTestcase,
)


@pytest.mark.rabbit
class TestMiddlewares(MiddlewareTestcase):
    broker_class = RabbitBroker


@pytest.mark.rabbit()
class TestExceptionMiddlewares(ExceptionMiddlewareTestcase):
    broker_class = RabbitBroker
