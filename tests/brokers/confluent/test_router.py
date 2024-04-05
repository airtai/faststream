from typing import Any

import pytest

from faststream.confluent import KafkaPublisher, KafkaRoute, KafkaRouter
from tests.brokers.base.router import RouterLocalTestcase, RouterTestcase


@pytest.mark.confluent()
class TestRouter(RouterTestcase):
    broker_class = KafkaRouter
    route_class = KafkaRoute
    timeout: int = 10
    publisher_class = KafkaPublisher
    subscriber_kwargs: dict[str, Any] = {"auto_offset_reset": "earliest"}


class TestRouterLocal(RouterLocalTestcase):
    broker_class = KafkaRouter
    route_class = KafkaRoute
    timeout: int = 10
    publisher_class = KafkaPublisher
    subscriber_kwargs: dict[str, Any] = {"auto_offset_reset": "earliest"}
