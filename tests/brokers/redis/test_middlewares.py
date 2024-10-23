from typing import Any

import pytest

from faststream.redis import RedisBroker
from tests.brokers.base.middlewares import (
    ExceptionMiddlewareTestcase,
    MiddlewareTestcase,
)


@pytest.mark.redis()
class TestMiddlewares(MiddlewareTestcase):
    def get_broker(self, apply_types: bool = False, **kwargs: Any) -> RedisBroker:
        return RedisBroker(apply_types=apply_types, **kwargs)


@pytest.mark.redis()
class TestExceptionMiddlewares(ExceptionMiddlewareTestcase):
    def get_broker(self, apply_types: bool = False, **kwargs: Any) -> RedisBroker:
        return RedisBroker(apply_types=apply_types, **kwargs)
