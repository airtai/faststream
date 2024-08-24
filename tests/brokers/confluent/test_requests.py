import pytest

from faststream import BaseMiddleware
from faststream.confluent import KafkaBroker, KafkaRouter, TestKafkaBroker
from tests.brokers.base.requests import RequestsTestcase

from .basic import ConfluentTestcaseConfig


class Mid(BaseMiddleware):
    async def on_receive(self) -> None:
        self.msg._raw_msg = self.msg._raw_msg * 2

    async def consume_scope(self, call_next, msg):
        msg._decoded_body = msg._decoded_body * 2
        return await call_next(msg)


@pytest.mark.asyncio
class TestRequestTestClient(ConfluentTestcaseConfig, RequestsTestcase):
    def get_middleware(self, **kwargs):
        return Mid

    def get_broker(self, **kwargs):
        return KafkaBroker(**kwargs)

    def get_router(self, **kwargs):
        return KafkaRouter(**kwargs)

    def patch_broker(self, broker, **kwargs):
        return TestKafkaBroker(broker, **kwargs)
