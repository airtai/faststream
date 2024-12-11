from typing import Any

from faststream.rabbit.prometheus import RabbitPrometheusMiddleware
from tests.brokers.rabbit.basic import RabbitTestcaseConfig


class RabbitPrometheusSettings(RabbitTestcaseConfig):
    messaging_system = "rabbitmq"

    def get_middleware(self, **kwargs: Any) -> RabbitPrometheusMiddleware:
        return RabbitPrometheusMiddleware(**kwargs)
