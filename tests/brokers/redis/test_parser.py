import pytest

from faststream.redis import RedisBroker
from tests.brokers.base.parser import CustomParserTestcase


@pytest.mark.redis()
class TestCustomParser(CustomParserTestcase):  # noqa: D101
    broker_class = RedisBroker
