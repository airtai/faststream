import pytest

from faststream.confluent import KafkaBroker
from tests.brokers.base.middlewares import MiddlewareTestcase

from .basic import ConfluentTestcaseConfig


@pytest.mark.confluent
class TestMiddlewares(ConfluentTestcaseConfig, MiddlewareTestcase):
    broker_class = KafkaBroker
