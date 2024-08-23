import asyncio
from typing import List
from unittest.mock import Mock

import pytest

from faststream.confluent.fastapi import KafkaRouter
from faststream.confluent.testing import TestKafkaBroker, build_message
from tests.brokers.base.fastapi import FastAPILocalTestcase, FastAPITestcase

from .basic import ConfluentTestcaseConfig


@pytest.mark.confluent
class TestConfluentRouter(ConfluentTestcaseConfig, FastAPITestcase):
    router_class = KafkaRouter

    async def test_batch_real(
        self,
        mock: Mock,
        queue: str,
        event: asyncio.Event,
    ):
        router = KafkaRouter()

        args, kwargs = self.get_subscriber_params(queue, batch=True)

        @router.subscriber(*args, **kwargs)
        async def hello(msg: List[str]):
            event.set()
            return mock(msg)

        async with router.broker:
            await router.broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(router.broker.publish("hi", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=self.timeout,
            )

        assert event.is_set()
        mock.assert_called_with(["hi"])


class TestRouterLocal(ConfluentTestcaseConfig, FastAPILocalTestcase):
    router_class = KafkaRouter
    broker_test = staticmethod(TestKafkaBroker)
    build_message = staticmethod(build_message)

    async def test_batch_testclient(
        self,
        mock: Mock,
        queue: str,
        event: asyncio.Event,
    ):
        router = KafkaRouter()

        args, kwargs = self.get_subscriber_params(queue, batch=True)

        @router.subscriber(*args, **kwargs)
        async def hello(msg: List[str]):
            event.set()
            return mock(msg)

        async with TestKafkaBroker(router.broker):
            await asyncio.wait(
                (
                    asyncio.create_task(router.broker.publish("hi", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=self.timeout,
            )

        assert event.is_set()
        mock.assert_called_with(["hi"])
