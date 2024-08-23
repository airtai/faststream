import pytest

from faststream.redis import RedisBroker, RedisRouter, TestRedisBroker
from tests.brokers.base.requests import RequestsTestcase


@pytest.mark.asyncio
class RedisRequestsTestcase(RequestsTestcase):
    def get_broker(self):
        return RedisBroker()

    def get_router(self):
        return RedisRouter()


@pytest.mark.redis
class TestRealRequests(RedisRequestsTestcase):
    pass


class TestRequestTestClient(RedisRequestsTestcase):
    def patch_broker(self, broker):
        return TestRedisBroker(broker)
