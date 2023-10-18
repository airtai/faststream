import pytest

from faststream.redis import RedisRoute, RedisRouter
from tests.brokers.base.router import RouterLocalTestcase, RouterTestcase


@pytest.mark.redis
class TestRouter(RouterTestcase):
    broker_class = RedisRouter
    route_class = RedisRoute


class TestRouterLocal(RouterLocalTestcase):
    broker_class = RedisRouter
    route_class = RedisRoute
