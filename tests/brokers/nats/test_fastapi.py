import pytest

from faststream.nats.fastapi import NatsRouter
from faststream.nats.test import TestNatsBroker, build_message
from tests.brokers.base.fastapi import FastAPILocalTestcase, FastAPITestcase


@pytest.mark.nats
class TestRouter(FastAPITestcase):
    router_class = NatsRouter


class TestRouterLocal(FastAPILocalTestcase):
    router_class = NatsRouter
    broker_test = staticmethod(TestNatsBroker)
    build_message = staticmethod(build_message)
