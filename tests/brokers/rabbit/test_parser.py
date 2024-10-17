from typing import Any

import pytest

from faststream.rabbit import RabbitBroker
from tests.brokers.base.parser import CustomParserTestcase


@pytest.mark.rabbit()
class TestCustomParser(CustomParserTestcase):
    def get_broker(self, apply_types: bool = False, **kwargs: Any) -> RabbitBroker:
        return RabbitBroker(apply_types=apply_types, **kwargs)
