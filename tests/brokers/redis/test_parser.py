from typing import Any

import pytest

from faststream.redis import RedisBroker
from tests.brokers.base.parser import CustomParserTestcase


@pytest.mark.redis()
class TestCustomParser(CustomParserTestcase):
    def get_broker(self, apply_types: bool = False, **kwargs: Any) -> RedisBroker:
        return RedisBroker(apply_types=apply_types, **kwargs)
