from typing import Any

import pytest

from faststream.rabbit import RabbitBroker
from tests.brokers.base.middlewares import (
    ExceptionMiddlewareTestcase,
    MiddlewareTestcase,
)


@pytest.mark.rabbit
class TestMiddlewares(MiddlewareTestcase):
    def get_broker(self, apply_types: bool = False, **kwargs: Any) -> RabbitBroker:
        return RabbitBroker(apply_types=apply_types, **kwargs)


@pytest.mark.rabbit
class TestExceptionMiddlewares(ExceptionMiddlewareTestcase):
    def get_broker(self, apply_types: bool = False, **kwargs: Any) -> RabbitBroker:
        return RabbitBroker(apply_types=apply_types, **kwargs)
