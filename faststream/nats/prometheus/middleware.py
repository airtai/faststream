from typing import TYPE_CHECKING, List, Optional

from faststream.nats.prometheus.provider import settings_provider_factory
from faststream.prometheus.middleware import BasePrometheusMiddleware

if TYPE_CHECKING:
    from prometheus_client import CollectorRegistry


class NatsPrometheusMiddleware(BasePrometheusMiddleware):
    def __init__(
        self,
        *,
        registry: "CollectorRegistry",
        app_name: str = "faststream",
        metrics_prefix: str = "faststream",
        received_messages_size_buckets: Optional[List[int]] = None,
    ) -> None:
        super().__init__(
            settings_provider_factory=settings_provider_factory,
            registry=registry,
            app_name=app_name,
            metrics_prefix=metrics_prefix,
            received_messages_size_buckets=received_messages_size_buckets,
        )
