from typing import Type

from faststream.asyncapi.version import AsyncAPIVersion
from faststream.nats import TestNatsBroker
from faststream.nats.fastapi import NatsRouter
from tests.asyncapi.base.v3_0_0.arguments import FastAPICompatible
from tests.asyncapi.base.v3_0_0.fastapi import FastAPITestCase
from tests.asyncapi.base.v3_0_0.publisher import PublisherTestcase


class TestRouterArguments(FastAPITestCase, FastAPICompatible):
    broker_factory = staticmethod(lambda: NatsRouter(asyncapi_version=AsyncAPIVersion.v3_0))
    router_factory = NatsRouter
    broker_wrapper = staticmethod(TestNatsBroker)

    def build_app(self, router):
        return router


class TestRouterPublisher(PublisherTestcase):
    broker_factory = staticmethod(lambda: NatsRouter(asyncapi_version=AsyncAPIVersion.v3_0))

    def build_app(self, router):
        return router