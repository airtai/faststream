import pytest

from faststream.nats import NatsBroker
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


@pytest.mark.nats
class TestMiddlewaresOrder(MiddlewaresOrderTestcase):
    broker_class = NatsBroker
