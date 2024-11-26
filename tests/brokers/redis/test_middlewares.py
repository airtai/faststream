import pytest

from faststream.redis import RedisBroker
from tests.brokers.base.middlewares import (
    ExceptionMiddlewareTestcase,
    MiddlewareTestcase,
    MiddlewaresOrderTestcase,
)


@pytest.mark.redis
class TestMiddlewares(MiddlewareTestcase):
    broker_class = RedisBroker


@pytest.mark.redis
class TestExceptionMiddlewares(ExceptionMiddlewareTestcase):
    broker_class = RedisBroker


@pytest.mark.redis
class TestMiddlewaresOrder(MiddlewaresOrderTestcase):
    broker_class = RedisBroker
