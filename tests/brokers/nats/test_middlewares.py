import pytest

from faststream.nats import NatsBroker, TestNatsBroker
from tests.brokers.base.middlewares import (
    ExceptionMiddlewareTestcase,
    MiddlewareTestcase,
    MiddlewaresOrderTestcase,
)


@pytest.mark.nats
class TestMiddlewares(MiddlewareTestcase):
    broker_class = NatsBroker


@pytest.mark.nats
class TestExceptionMiddlewares(ExceptionMiddlewareTestcase):
    broker_class = NatsBroker


class TestMiddlewaresOrder(MiddlewaresOrderTestcase):
    broker_class = NatsBroker

    def patch_broker(self, broker: NatsBroker) -> TestNatsBroker:
        return TestNatsBroker(broker)
