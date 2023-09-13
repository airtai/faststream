from typing import Type

from faststream.rabbit.fastapi import RabbitRouter
from faststream.rabbit.test import TestRabbitBroker
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
