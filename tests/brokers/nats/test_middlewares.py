import pytest

from faststream.nats import NatsBroker
from tests.brokers.base.middlewares import MiddlewareTestcase


@pytest.mark.nats()
class TestMiddlewares(MiddlewareTestcase):  # noqa: D101
    broker_class = NatsBroker
