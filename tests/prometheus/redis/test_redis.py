import asyncio
from unittest.mock import Mock

import pytest
from prometheus_client import CollectorRegistry

from faststream.redis import ListSub, RedisBroker, RedisMessage
from faststream.redis.prometheus.middleware import RedisPrometheusMiddleware
from tests.brokers.redis.test_consume import TestConsume
from tests.brokers.redis.test_publish import TestPublish
from tests.prometheus.basic import LocalPrometheusTestcase


@pytest.mark.redis
class TestPrometheus(LocalPrometheusTestcase):
    broker_class = RedisBroker
    middleware_class = RedisPrometheusMiddleware
    message_class = RedisMessage

    async def test_metrics_batch(
        self,
        event: asyncio.Event,
        queue: str,
    ):
        middleware = self.middleware_class(registry=CollectorRegistry())
        metrics_mock = Mock()
        middleware._metrics = metrics_mock

        broker = self.broker_class(middlewares=(middleware,))

        args, kwargs = self.get_subscriber_params(list=ListSub(queue, batch=True))

        message_class = self.message_class
        message = None

        @broker.subscriber(*args, **kwargs)
        async def handler(m: message_class):
            event.set()

            nonlocal message
            message = m

        async with broker:
            await broker.start()
            tasks = (
                asyncio.create_task(broker.publish_batch("hello", "world", list=queue)),
                asyncio.create_task(event.wait()),
            )
            await asyncio.wait(tasks, timeout=self.timeout)

        assert event.is_set()
        self.assert_consume_metrics(
            metrics=metrics_mock, message=message, exception_class=None
        )
        self.assert_publish_metrics(metrics=metrics_mock)


@pytest.mark.redis
class TestPublishWithPrometheus(TestPublish):
    def get_broker(self, apply_types: bool = False):
        return RedisBroker(
            middlewares=(RedisPrometheusMiddleware(registry=CollectorRegistry()),),
            apply_types=apply_types,
        )


@pytest.mark.redis
class TestConsumeWithPrometheus(TestConsume):
    def get_broker(self, apply_types: bool = False):
        return RedisBroker(
            middlewares=(RedisPrometheusMiddleware(registry=CollectorRegistry()),),
            apply_types=apply_types,
        )
