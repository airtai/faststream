from typing import Type

from faststream.kafka.fastapi import KafkaRouter
from faststream.kafka.test import TestKafkaBroker
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
