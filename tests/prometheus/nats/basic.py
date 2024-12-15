from typing import Any

from faststream.nats import NatsBroker
from faststream.nats.prometheus import NatsPrometheusMiddleware
from tests.brokers.nats.basic import NatsTestcaseConfig


class NatsPrometheusSettings(NatsTestcaseConfig):
    messaging_system = "nats"

    def get_broker(self, apply_types=False, **kwargs: Any) -> NatsBroker:
        return NatsBroker(apply_types=apply_types, **kwargs)

    def get_middleware(self, **kwargs: Any) -> NatsPrometheusMiddleware:
        return NatsPrometheusMiddleware(**kwargs)
