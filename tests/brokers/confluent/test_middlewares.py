from typing import Any, ClassVar, Dict

import pytest

from faststream.confluent import KafkaBroker
from tests.brokers.base.middlewares import (
    ExceptionMiddlewareTestcase,
    MiddlewareTestcase,
)


@pytest.mark.confluent()
class TestMiddlewares(MiddlewareTestcase):
    broker_class = KafkaBroker
    timeout: int = 10
    subscriber_kwargs: ClassVar[Dict[str, Any]] = {
        "auto_offset_reset": "earliest"}


@pytest.mark.confluent()
class TestExceptionMiddlewares(ExceptionMiddlewareTestcase):
    broker_class = KafkaBroker
    timeout: int = 10
    subscriber_kwargs: ClassVar[Dict[str, Any]] = {
        "auto_offset_reset": "earliest"
    }
