from typing import Any

import pytest

from faststream import BaseMiddleware
from faststream.confluent import KafkaBroker, KafkaRouter, TestKafkaBroker
from tests.brokers.base.requests import RequestsTestcase

from .basic import ConfluentTestcaseConfig


class Mid(BaseMiddleware):
    async def on_receive(self) -> None:
        self.msg._raw_msg *= 2

    async def consume_scope(self, call_next, msg):
        msg.body *= 2
        return await call_next(msg)


@pytest.mark.asyncio()
class TestRequestTestClient(ConfluentTestcaseConfig, RequestsTestcase):
    def get_middleware(self, **kwargs: Any):
        return Mid

    def get_router(self, **kwargs: Any):
        return KafkaRouter(**kwargs)

    def get_broker(self, apply_types: bool = False, **kwargs: Any) -> KafkaBroker:
        return KafkaBroker(apply_types=apply_types, **kwargs)

    def patch_broker(self, broker: KafkaBroker, **kwargs: Any) -> TestKafkaBroker:
        return TestKafkaBroker(broker, **kwargs)
