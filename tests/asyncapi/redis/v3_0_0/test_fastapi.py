from typing import Type

from faststream.asyncapi.version import AsyncAPIVersion
from faststream.redis import TestRedisBroker
from faststream.redis.fastapi import RedisRouter
from tests.asyncapi.base.v3_0_0.arguments import FastAPICompatible
from tests.asyncapi.base.v3_0_0.fastapi import FastAPITestCase
from tests.asyncapi.base.v3_0_0.publisher import PublisherTestcase


class TestRouterArguments(FastAPITestCase, FastAPICompatible):
    broker_factory = staticmethod(lambda: RedisRouter(asyncapi_version=AsyncAPIVersion.v3_0))
    router_factory = RedisRouter
    broker_wrapper = staticmethod(TestRedisBroker)

    def build_app(self, router):
        return router


class TestRouterPublisher(PublisherTestcase):
    broker_factory = staticmethod(lambda: RedisRouter(asyncapi_version=AsyncAPIVersion.v3_0))

    def build_app(self, router):
        return router
