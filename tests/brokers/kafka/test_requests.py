from typing import Any

import pytest

from faststream import BaseMiddleware
from faststream.kafka import KafkaBroker, KafkaRouter, TestKafkaBroker
from tests.brokers.base.requests import RequestsTestcase


class Mid(BaseMiddleware):
    async def on_receive(self) -> None:
        self.msg.value = self.msg.value * 2

    async def consume_scope(self, call_next, msg):
        msg._decoded_body = msg._decoded_body * 2
        return await call_next(msg)


@pytest.mark.asyncio
class TestRequestTestClient(RequestsTestcase):
    def get_middleware(self, **kwargs: Any):
        return Mid

    def get_router(self, **kwargs: Any):
        return KafkaRouter(**kwargs)

    def get_broker(self, apply_types: bool = False, **kwargs: Any) -> KafkaBroker:
        return KafkaBroker(apply_types=apply_types, **kwargs)

    def patch_broker(self, broker: KafkaBroker, **kwargs: Any) -> TestKafkaBroker:
        return TestKafkaBroker(broker, **kwargs)
