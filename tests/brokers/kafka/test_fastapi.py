import asyncio
from typing import List
from unittest.mock import Mock

import pytest

from faststream.kafka import KafkaRouter
from faststream.kafka.fastapi import KafkaRouter as StreamRouter
from faststream.kafka.testing import TestKafkaBroker, build_message
from tests.brokers.base.fastapi import FastAPILocalTestcase, FastAPITestcase


@pytest.mark.kafka
class TestKafkaRouter(FastAPITestcase):
    router_class = StreamRouter
    broker_router_class = KafkaRouter

    async def test_batch_real(
        self,
        mock: Mock,
        queue: str,
        event: asyncio.Event,
    ):
        router = self.router_class()

        @router.subscriber(queue, batch=True)
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
                timeout=3,
            )

        assert event.is_set()
        mock.assert_called_with(["hi"])


class TestRouterLocal(FastAPILocalTestcase):
    router_class = StreamRouter
    broker_router_class = KafkaRouter
    broker_test = staticmethod(TestKafkaBroker)
    build_message = staticmethod(build_message)

    async def test_batch_testclient(
        self,
        mock: Mock,
        queue: str,
        event: asyncio.Event,
    ):
        router = self.router_class()

        @router.subscriber(queue, batch=True)
        async def hello(msg: List[str]):
            event.set()
            return mock(msg)

        async with TestKafkaBroker(router.broker):
            await asyncio.wait(
                (
                    asyncio.create_task(router.broker.publish("hi", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        assert event.is_set()
        mock.assert_called_with(["hi"])
