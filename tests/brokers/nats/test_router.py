import pytest

from faststream.nats import NatsRoute, NatsRouter
from tests.brokers.base.router import RouterLocalTestcase, RouterTestcase


@pytest.mark.nats
class TestRouter(RouterTestcase):
    broker_class = NatsRouter
    route_class = NatsRoute

class TestRouterLocal(RouterLocalTestcase):
    broker_class = NatsRouter
    route_class = NatsRoute
