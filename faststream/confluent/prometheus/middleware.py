from typing import TYPE_CHECKING

from faststream.confluent.prometheus.provider import settings_provider_factory
from faststream.prometheus.middleware import BasePrometheusMiddleware

if TYPE_CHECKING:
    from prometheus_client import CollectorRegistry


class KafkaPrometheusMiddleware(BasePrometheusMiddleware):
    def __init__(
        self,
        *,
        registry: "CollectorRegistry",
    ):
        super().__init__(
            settings_provider_factory=settings_provider_factory,
            registry=registry,
        )
