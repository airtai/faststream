import asyncio
from typing import Any
from unittest.mock import Mock

import pytest
from prometheus_client import CollectorRegistry

from faststream import Context
from faststream.nats import JStream, NatsBroker, PullSub
from faststream.nats.prometheus.middleware import NatsPrometheusMiddleware
from tests.brokers.nats.test_consume import TestConsume
from tests.brokers.nats.test_publish import TestPublish
from tests.prometheus.basic import LocalPrometheusTestcase, LocalRPCPrometheusTestcase

from .basic import NatsPrometheusSettings


@pytest.fixture()
def stream(queue):
    return JStream(queue)


@pytest.mark.nats()
class TestPrometheus(
    NatsPrometheusSettings, LocalPrometheusTestcase, LocalRPCPrometheusTestcase
):
    async def test_metrics_batch(
        self,
        queue: str,
        stream: JStream,
    ) -> None:
        event = asyncio.Event()

        middleware = self.get_middleware(registry=CollectorRegistry())
        metrics_manager_mock = Mock()
        middleware._metrics_manager = metrics_manager_mock

        broker = self.get_broker(apply_types=True, middlewares=(middleware,))

        args, kwargs = self.get_subscriber_params(
            queue,
            stream=stream,
            pull_sub=PullSub(1, batch=True, timeout=self.timeout),
        )
        message = None

        @broker.subscriber(*args, **kwargs)
        async def handler(m=Context("message")):
            event.set()

            nonlocal message
            message = m

        async with broker:
            await broker.start()
            tasks = (
                asyncio.create_task(broker.publish("hello", queue)),
                asyncio.create_task(event.wait()),
            )
            await asyncio.wait(tasks, timeout=self.timeout)

        assert event.is_set()
        self.assert_consume_metrics(
            metrics_manager=metrics_manager_mock, message=message, exception_class=None
        )
        self.assert_publish_metrics(metrics_manager=metrics_manager_mock)


@pytest.mark.nats()
class TestPublishWithPrometheus(TestPublish):
    def get_broker(self, apply_types: bool = False, **kwargs: Any) -> NatsBroker:
        return NatsBroker(
            middlewares=(NatsPrometheusMiddleware(registry=CollectorRegistry()),),
            apply_types=apply_types,
            **kwargs,
        )


@pytest.mark.nats()
class TestConsumeWithPrometheus(TestConsume):
    def get_broker(self, apply_types: bool = False, **kwargs: Any) -> NatsBroker:
        return NatsBroker(
            middlewares=(NatsPrometheusMiddleware(registry=CollectorRegistry()),),
            apply_types=apply_types,
            **kwargs,
        )
