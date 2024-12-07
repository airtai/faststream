from typing import Any

from faststream.redis import RedisBroker
from faststream.redis.prometheus import RedisPrometheusMiddleware
from tests.brokers.redis.basic import RedisTestcaseConfig


class RedisPrometheusSettings(RedisTestcaseConfig):
    messaging_system = "redis"

    def get_broker(self, apply_types=False, **kwargs: Any) -> RedisBroker:
        return RedisBroker(apply_types=apply_types, **kwargs)

    def get_middleware(self, **kwargs: Any) -> RedisPrometheusMiddleware:
        return RedisPrometheusMiddleware(**kwargs)
