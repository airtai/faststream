import pytest

from faststream import BaseMiddleware
from faststream.rabbit import RabbitBroker, RabbitRouter, TestRabbitBroker
from tests.brokers.base.requests import RequestsTestcase


class Mid(BaseMiddleware):
    async def on_receive(self) -> None:
        self.msg._Message__lock = False
        self.msg.body = self.msg.body * 2

    async def consume_scope(self, call_next, msg):
        msg._decoded_body = msg._decoded_body * 2
        return await call_next(msg)


@pytest.mark.asyncio
class RabbitRequestsTestcase(RequestsTestcase):
    def get_middleware(self, **kwargs):
        return Mid

    def get_broker(self, **kwargs):
        return RabbitBroker(**kwargs)

    def get_router(self, **kwargs):
        return RabbitRouter(**kwargs)


@pytest.mark.rabbit
class TestRealRequests(RabbitRequestsTestcase):
    pass


@pytest.mark.asyncio
class TestRequestTestClient(RabbitRequestsTestcase):
    def patch_broker(self, broker, **kwargs):
        return TestRabbitBroker(broker, **kwargs)
