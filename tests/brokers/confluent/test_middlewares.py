from typing import Any

import pytest

from faststream.confluent import KafkaBroker
from tests.brokers.base.middlewares import (
    ExceptionMiddlewareTestcase,
    MiddlewareTestcase,
)

from .basic import ConfluentTestcaseConfig


@pytest.mark.confluent()
class TestMiddlewares(ConfluentTestcaseConfig, MiddlewareTestcase):
    def get_broker(self, apply_types: bool = False, **kwargs: Any) -> KafkaBroker:
        return KafkaBroker(apply_types=apply_types, **kwargs)


@pytest.mark.confluent()
class TestExceptionMiddlewares(ConfluentTestcaseConfig, ExceptionMiddlewareTestcase):
    def get_broker(self, apply_types: bool = False, **kwargs: Any) -> KafkaBroker:
        return KafkaBroker(apply_types=apply_types, **kwargs)
