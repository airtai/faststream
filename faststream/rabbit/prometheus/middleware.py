from typing import TYPE_CHECKING

from faststream.prometheus.middleware import BasePrometheusMiddleware
from faststream.rabbit.prometheus.provider import RabbitMetricsSettingsProvider

if TYPE_CHECKING:
    from prometheus_client import CollectorRegistry


class RabbitPrometheusMiddleware(BasePrometheusMiddleware):
    def __init__(
        self,
        *,
        registry: "CollectorRegistry",
    ) -> None:
        super().__init__(
            settings_provider_factory=lambda _: RabbitMetricsSettingsProvider(),
            registry=registry,
        )
