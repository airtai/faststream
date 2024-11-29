import pytest

from faststream.confluent import KafkaBroker, TestKafkaBroker
from tests.brokers.base.middlewares import (
    ExceptionMiddlewareTestcase,
    MiddlewareTestcase,
    MiddlewaresOrderTestcase,
)

from .basic import ConfluentTestcaseConfig


@pytest.mark.confluent
class TestMiddlewares(ConfluentTestcaseConfig, MiddlewareTestcase):
    broker_class = KafkaBroker


@pytest.mark.confluent
class TestExceptionMiddlewares(ConfluentTestcaseConfig, ExceptionMiddlewareTestcase):
    broker_class = KafkaBroker


class TestMiddlewaresOrder(MiddlewaresOrderTestcase):
    broker_class = KafkaBroker

    def patch_broker(self, broker: KafkaBroker) -> TestKafkaBroker:
        return TestKafkaBroker(broker)
