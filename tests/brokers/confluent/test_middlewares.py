import pytest

from faststream.confluent import KafkaBroker
from tests.brokers.base.middlewares import (
    ExceptionMiddlewareTestcase,
    MiddlewareTestcase,
)

from .basic import ConfluentTestcaseConfig


@pytest.mark.confluent
class TestMiddlewares(ConfluentTestcaseConfig, MiddlewareTestcase):
    broker_class = KafkaBroker


@pytest.mark.confluent
class TestExceptionMiddlewares(ConfluentTestcaseConfig, ExceptionMiddlewareTestcase):
    broker_class = KafkaBroker
