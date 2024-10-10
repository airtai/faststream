from typing import Any

import pytest

from faststream.kafka import KafkaBroker
from tests.brokers.base.middlewares import (
    ExceptionMiddlewareTestcase,
    MiddlewareTestcase,
)


@pytest.mark.kafka()
class TestMiddlewares(MiddlewareTestcase):
    def get_broker(self, apply_types: bool = False, **kwargs: Any) -> KafkaBroker:
        return KafkaBroker(apply_types=apply_types, **kwargs)


@pytest.mark.kafka()
class TestExceptionMiddlewares(ExceptionMiddlewareTestcase):
    def get_broker(self, apply_types: bool = False, **kwargs: Any) -> KafkaBroker:
        return KafkaBroker(apply_types=apply_types, **kwargs)
