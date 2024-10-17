from typing import Any

import pytest

from faststream.nats import NatsBroker
from tests.brokers.base.middlewares import (
    ExceptionMiddlewareTestcase,
    MiddlewareTestcase,
)


@pytest.mark.nats()
class TestMiddlewares(MiddlewareTestcase):
    def get_broker(self, apply_types: bool = False, **kwargs: Any) -> NatsBroker:
        return NatsBroker(apply_types=apply_types, **kwargs)


@pytest.mark.nats()
class TestExceptionMiddlewares(ExceptionMiddlewareTestcase):
    def get_broker(self, apply_types: bool = False, **kwargs: Any) -> NatsBroker:
        return NatsBroker(apply_types=apply_types, **kwargs)
