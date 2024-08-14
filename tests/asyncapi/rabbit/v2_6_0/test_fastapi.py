from typing import Type

from faststream.specification.asyncapi.generate import get_app_schema
from faststream.rabbit.fastapi import RabbitRouter
from faststream.rabbit.testing import TestRabbitBroker
from faststream.security import SASLPlaintext
from tests.asyncapi.base.arguments import FastAPICompatible
from tests.asyncapi.base.fastapi import FastAPITestCase
from tests.asyncapi.base.publisher import PublisherTestcase


class TestRouterArguments(FastAPITestCase, FastAPICompatible):
    broker_class: Type[RabbitRouter] = RabbitRouter
    broker_wrapper = staticmethod(TestRabbitBroker)

    def build_app(self, router):
        return router


class TestRouterPublisher(PublisherTestcase):
    broker_class = RabbitRouter

    def build_app(self, router):
        return router


def test_fastapi_security_schema():
    security = SASLPlaintext(username="user", password="pass", use_ssl=False)

    broker = RabbitRouter(security=security)

    schema = get_app_schema(broker).to_jsonable()

    assert schema["servers"]["development"] == {
        "protocol": "amqp",
        "protocolVersion": "0.9.1",
        "security": [{"user-password": []}],
        "url": "amqp://user:pass@localhost:5672/",  # pragma: allowlist secret
    }
    assert schema["components"]["securitySchemes"] == {
        "user-password": {"type": "userPassword"}
    }
