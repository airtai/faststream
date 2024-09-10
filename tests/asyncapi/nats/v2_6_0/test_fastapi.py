from typing import Type

from faststream.nats import TestNatsBroker
from faststream.nats.fastapi import NatsRouter
from tests.asyncapi.base.v2_6_0.arguments import FastAPICompatible
from tests.asyncapi.base.v2_6_0.fastapi import FastAPITestCase
from tests.asyncapi.base.v2_6_0.publisher import PublisherTestcase


class TestRouterArguments(FastAPITestCase, FastAPICompatible):
    broker_class: Type[NatsRouter] = NatsRouter
    broker_wrapper = staticmethod(TestNatsBroker)

    def build_app(self, router):
        return router


class TestRouterPublisher(PublisherTestcase):
    broker_class = NatsRouter

    def build_app(self, router):
        return router
