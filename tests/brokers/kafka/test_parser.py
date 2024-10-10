from typing import Any

import pytest

from faststream.kafka import KafkaBroker
from tests.brokers.base.parser import CustomParserTestcase


@pytest.mark.kafka()
class TestCustomParser(CustomParserTestcase):
    def get_broker(self, apply_types: bool = False, **kwargs: Any) -> KafkaBroker:
        return KafkaBroker(apply_types=apply_types, **kwargs)
