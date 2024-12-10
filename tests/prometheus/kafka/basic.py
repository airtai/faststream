from typing import Any

from faststream import AckPolicy
from faststream.kafka.prometheus import KafkaPrometheusMiddleware
from tests.brokers.kafka.basic import KafkaTestcaseConfig


class KafkaPrometheusSettings(KafkaTestcaseConfig):
    messaging_system = "kafka"

    def get_middleware(self, **kwargs: Any) -> KafkaPrometheusMiddleware:
        return KafkaPrometheusMiddleware(**kwargs)

    def get_subscriber_params(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> tuple[
        tuple[Any, ...],
        dict[str, Any],
    ]:
        args, kwargs = super().get_subscriber_params(*args, **kwargs)
        return args, {
            "group_id": "test",
            "ack_policy": AckPolicy.REJECT_ON_ERROR,
            **kwargs,
        }
