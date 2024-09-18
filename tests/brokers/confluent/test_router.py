from typing import Any

import pytest

from faststream.confluent import (
    KafkaBroker,
    KafkaPublisher,
    KafkaRoute,
    KafkaRouter,
    TestKafkaBroker,
)
from tests.brokers.base.router import RouterLocalTestcase, RouterTestcase

from .basic import ConfluentTestcaseConfig


@pytest.mark.confluent
class TestRouter(ConfluentTestcaseConfig, RouterTestcase):
    broker_class = KafkaRouter
    route_class = KafkaRoute
    publisher_class = KafkaPublisher

    def get_broker(self, apply_types: bool = False, **kwargs: Any) -> KafkaBroker:
        return KafkaBroker(apply_types=apply_types, **kwargs)


class TestRouterLocal(ConfluentTestcaseConfig, RouterLocalTestcase):
    broker_class = KafkaRouter
    route_class = KafkaRoute
    publisher_class = KafkaPublisher

    def get_broker(self, apply_types: bool = False, **kwargs: Any) -> KafkaBroker:
        return KafkaBroker(apply_types=apply_types, **kwargs)

    def patch_broker(self, broker: KafkaBroker, **kwargs: Any) -> TestKafkaBroker:
        return TestKafkaBroker(broker, **kwargs)
