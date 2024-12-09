from typing import Any

from faststream import AckPolicy
from faststream.confluent import KafkaBroker
from faststream.confluent.prometheus import KafkaPrometheusMiddleware
from tests.brokers.confluent.basic import ConfluentTestcaseConfig


class KafkaPrometheusSettings(ConfluentTestcaseConfig):
    messaging_system = "kafka"

    def get_broker(self, apply_types=False, **kwargs: Any) -> KafkaBroker:
        return KafkaBroker(apply_types=apply_types, **kwargs)

    def get_middleware(self, **kwargs: Any) -> KafkaPrometheusMiddleware:
        return KafkaPrometheusMiddleware(**kwargs)

    def get_subscriber_params(
        self,
        *topics: Any,
        **kwargs: Any,
    ) -> tuple[
        tuple[Any, ...],
        dict[str, Any],
    ]:
        topics, kwargs = super().get_subscriber_params(*topics, **kwargs)

        return topics, {
            "group_id": "test",
            "ack_policy": AckPolicy.REJECT_ON_ERROR,
            **kwargs,
        }
