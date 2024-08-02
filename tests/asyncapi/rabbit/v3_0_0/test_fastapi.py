from faststream.asyncapi.generate import get_app_schema
from faststream.asyncapi.version import AsyncAPIVersion
from faststream.rabbit.fastapi import RabbitRouter
from faststream.rabbit.testing import TestRabbitBroker
from faststream.security import SASLPlaintext
from tests.asyncapi.base.v3_0_0.arguments import FastAPICompatible
from tests.asyncapi.base.v3_0_0.fastapi import FastAPITestCase
from tests.asyncapi.base.v3_0_0.publisher import PublisherTestcase


class TestRouterArguments(FastAPITestCase, FastAPICompatible):
    broker_factory = staticmethod(lambda: RabbitRouter(asyncapi_version=AsyncAPIVersion.v3_0))
    router_factory = RabbitRouter
    broker_wrapper = staticmethod(TestRabbitBroker)

    def build_app(self, router):
        return router


class TestRouterPublisher(PublisherTestcase):
    broker_factory = staticmethod(lambda: RabbitRouter(asyncapi_version=AsyncAPIVersion.v3_0))

    def build_app(self, router):
        return router


def test_fastapi_security_schema():
    security = SASLPlaintext(username="user", password="pass", use_ssl=False)

    router = RabbitRouter(security=security, asyncapi_version=AsyncAPIVersion.v3_0)

    schema = get_app_schema(router,).to_jsonable()

    assert schema["servers"]["development"] == {
        "protocol": "amqp",
        "protocolVersion": "0.9.1",
        "security": [{"user-password": []}],
        "host": "user:pass@localhost:5672",  # pragma: allowlist secret
        "pathname": "/",  # pragma: allowlist secret
    }
    assert schema["components"]["securitySchemes"] == {
        "user-password": {"type": "userPassword"}
    }