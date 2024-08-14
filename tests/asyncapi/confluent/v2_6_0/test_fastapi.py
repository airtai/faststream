from typing import Type

from faststream.specification.asyncapi.generate import get_app_schema
from faststream.confluent.fastapi import KafkaRouter
from faststream.confluent.testing import TestKafkaBroker
from faststream.security import SASLPlaintext
from tests.asyncapi.base.arguments import FastAPICompatible
from tests.asyncapi.base.fastapi import FastAPITestCase
from tests.asyncapi.base.publisher import PublisherTestcase


class TestRouterArguments(FastAPITestCase, FastAPICompatible):
    broker_class: Type[KafkaRouter] = KafkaRouter
    broker_wrapper = staticmethod(TestKafkaBroker)

    def build_app(self, router):
        return router


class TestRouterPublisher(PublisherTestcase):
    broker_class = KafkaRouter

    def build_app(self, router):
        return router


def test_fastapi_security_schema():
    security = SASLPlaintext(username="user", password="pass", use_ssl=False)

    broker = KafkaRouter("localhost:9092", security=security)

    schema = get_app_schema(broker).to_jsonable()

    assert schema["servers"]["development"] == {
        "protocol": "kafka",
        "protocolVersion": "auto",
        "security": [{"user-password": []}],
        "url": "localhost:9092",
    }
    assert schema["components"]["securitySchemes"] == {
        "user-password": {"type": "userPassword"}
    }
