import pytest

from faststream.rabbit import RabbitBroker, TestRabbitBroker
from tests.brokers.base.middlewares import (
    ExceptionMiddlewareTestcase,
    MiddlewareTestcase,
    MiddlewaresOrderTestcase,
)


@pytest.mark.rabbit
class TestMiddlewares(MiddlewareTestcase):
    broker_class = RabbitBroker


@pytest.mark.rabbit
class TestExceptionMiddlewares(ExceptionMiddlewareTestcase):
    broker_class = RabbitBroker


class TestMiddlewaresOrder(MiddlewaresOrderTestcase):
    broker_class = RabbitBroker

    def patch_broker(self, broker: RabbitBroker) -> TestRabbitBroker:
        return TestRabbitBroker(broker)
