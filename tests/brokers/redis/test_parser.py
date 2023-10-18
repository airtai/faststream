import pytest

from faststream.redis import RedisBroker
from tests.brokers.base.parser import CustomParserTestcase


@pytest.mark.redis
class TestCustomParser(CustomParserTestcase):
    broker_class = RedisBroker
