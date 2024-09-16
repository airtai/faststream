from typing import TYPE_CHECKING

from faststream.prometheus.middleware import BasePrometheusMiddleware
from faststream.redis.prometheus.provider import attributes_provider_factory

if TYPE_CHECKING:
    from prometheus_client import CollectorRegistry


class RedisPrometheusMiddleware(BasePrometheusMiddleware):
    def __init__(
        self,
        *,
        registry: "CollectorRegistry",
    ):
        super().__init__(
            settings_provider_factory=attributes_provider_factory,
            registry=registry,
        )
