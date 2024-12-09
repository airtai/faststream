from typing import Any

from faststream.rabbit import RabbitBroker
from faststream.rabbit.prometheus import RabbitPrometheusMiddleware
from tests.brokers.rabbit.basic import RabbitTestcaseConfig


class RabbitPrometheusSettings(RabbitTestcaseConfig):
    messaging_system = "rabbitmq"

    def get_broker(self, apply_types=False, **kwargs: Any) -> RabbitBroker:
        return RabbitBroker(apply_types=apply_types, **kwargs)

    def get_middleware(self, **kwargs: Any) -> RabbitPrometheusMiddleware:
        return RabbitPrometheusMiddleware(**kwargs)
