from typing import Any

from faststream.nats import NatsBroker
from faststream.nats.prometheus import NatsPrometheusMiddleware


class NatsPrometheusSettings:
    messaging_system = "nats"

    def get_broker(self, apply_types=False, **kwargs: Any) -> NatsBroker:
        return NatsBroker(apply_types=apply_types, **kwargs)

    def get_middleware(self, **kwargs: Any) -> NatsPrometheusMiddleware:
        return NatsPrometheusMiddleware(**kwargs)
