import pytest

from faststream.rabbit import RabbitBroker
from tests.brokers.base.middlewares import MiddlewareTestcase


@pytest.mark.rabbit()
class TestMiddlewares(MiddlewareTestcase):  # noqa: D101
    broker_class = RabbitBroker
