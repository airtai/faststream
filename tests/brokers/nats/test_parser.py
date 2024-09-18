from typing import Any

import pytest

from faststream.nats import NatsBroker
from tests.brokers.base.parser import CustomParserTestcase


@pytest.mark.nats
class TestCustomParser(CustomParserTestcase):
    def get_broker(self, apply_types: bool = False, **kwargs: Any) -> NatsBroker:
        return NatsBroker(apply_types=apply_types, **kwargs)
