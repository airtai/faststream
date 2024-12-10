from typing import Any

from faststream.redis.prometheus import RedisPrometheusMiddleware
from tests.brokers.redis.basic import RedisTestcaseConfig


class RedisPrometheusSettings(RedisTestcaseConfig):
    messaging_system = "redis"

    def get_middleware(self, **kwargs: Any) -> RedisPrometheusMiddleware:
        return RedisPrometheusMiddleware(**kwargs)
