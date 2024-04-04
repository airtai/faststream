from typing import Any

import pytest

from unittest.mock import Mock

from faststream.confluent import KafkaBroker
from tests.brokers.base.middlewares import MiddlewareTestcase


@pytest.mark.confluent()
class TestMiddlewares(MiddlewareTestcase):
    broker_class = KafkaBroker
    timeout: int = 10
    subscriber_kwargs: dict[str, Any] = {"auto_offset_reset": "earliest"}
