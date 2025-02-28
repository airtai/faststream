import pytest

from faststream import BaseMiddleware
from faststream.redis import RedisBroker, RedisRouter, TestRedisBroker
from faststream.redis.parser import RawMessage
from tests.brokers.base.requests import RequestsTestcase


class Mid(BaseMiddleware):
    async def on_receive(self) -> None:
        raw_data, headers = RawMessage.parse(self.msg["data"])
        raw_data *= 2
        self.msg["data"] = RawMessage.encode(
            message=raw_data,
            reply_to=headers.get("reply_to"),
            headers=headers,
            correlation_id=headers.get("correlation_id"),
        )

    async def consume_scope(self, call_next, msg):
        msg._decoded_body = msg._decoded_body * 2
        return await call_next(msg)


@pytest.mark.asyncio
class RedisRequestsTestcase(RequestsTestcase):
    def get_middleware(self, **kwargs):
        return Mid

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
