import pytest

from faststream.kafka.fastapi import KafkaRouter
from faststream.kafka.test import TestKafkaBroker, build_message
from tests.brokers.base.fastapi import FastAPILocalTestcase, FastAPITestcase


@pytest.mark.kafka
class TestRabbitRouter(FastAPITestcase):
    router_class = KafkaRouter


class TestRouterLocal(FastAPILocalTestcase):
    router_class = KafkaRouter
    broker_test = staticmethod(TestKafkaBroker)
    build_message = staticmethod(build_message)
