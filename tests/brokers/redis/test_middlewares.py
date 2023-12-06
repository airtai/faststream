import pytest

from faststream.redis import RedisBroker
from tests.brokers.base.middlewares import MiddlewareTestcase


@pytest.mark.redis
class TestMiddlewares(MiddlewareTestcase):
    broker_class = RedisBroker
