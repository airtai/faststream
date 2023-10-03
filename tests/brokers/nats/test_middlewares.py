import pytest

from faststream.nats import NatsBroker
from tests.brokers.base.middlewares import MiddlewareTestcase


@pytest.mark.nats
class TestMiddlewares(MiddlewareTestcase):
    broker_class = NatsBroker
