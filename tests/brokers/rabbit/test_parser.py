import pytest

from propan.rabbit import RabbitBroker
from tests.brokers.base.parser import CustomParserTestcase


@pytest.mark.rabbit
class TestCustomParser(CustomParserTestcase):
    broker_class = RabbitBroker
