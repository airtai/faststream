import pytest

from faststream.redis.fastapi import RedisRouter
from faststream.redis.test import TestRedisBroker, build_message
from tests.brokers.base.fastapi import FastAPILocalTestcase, FastAPITestcase


@pytest.mark.redis
class TestRouter(FastAPITestcase):
    router_class = RedisRouter


class TestRouterLocal(FastAPILocalTestcase):
    router_class = RedisRouter
    broker_test = staticmethod(TestRedisBroker)
    build_message = staticmethod(build_message)
