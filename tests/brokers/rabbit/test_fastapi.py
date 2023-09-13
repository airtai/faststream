import pytest

from faststream.rabbit.fastapi import RabbitRouter
from faststream.rabbit.test import TestRabbitBroker, build_message
from tests.brokers.base.fastapi import FastAPILocalTestcase, FastAPITestcase


@pytest.mark.rabbit
class TestRouter(FastAPITestcase):
    router_class = RabbitRouter


class TestRouterLocal(FastAPILocalTestcase):
    router_class = RabbitRouter
    broker_test = staticmethod(TestRabbitBroker)
    build_message = staticmethod(build_message)
