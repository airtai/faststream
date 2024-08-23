import pytest

from faststream.redis import RedisBroker, RedisRouter, TestRedisBroker
from tests.brokers.base.requests import RequestsTestcase


@pytest.mark.asyncio
class RedisRequestsTestcase(RequestsTestcase):
    def get_broker(self, **kwargs):
        return RedisBroker(**kwargs)

    def get_router(self, **kwargs):
        return RedisRouter(**kwargs)


@pytest.mark.redis
class TestRealRequests(RedisRequestsTestcase):
    pass


class TestRequestTestClient(RedisRequestsTestcase):
    def patch_broker(self, broker, **kwargs):
        return TestRedisBroker(broker, **kwargs)
