import pytest

from faststream.redis import RedisBroker, TestRedisBroker
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


class TestMiddlewaresOrder(MiddlewaresOrderTestcase):
    broker_class = RedisBroker

    def patch_broker(self, broker: RedisBroker) -> TestRedisBroker:
        return TestRedisBroker(broker)
