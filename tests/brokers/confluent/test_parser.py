import pytest

from faststream.kafka import ConfluentKafkaBroker
from tests.brokers.base.parser import CustomParserTestcase


@pytest.mark.confluent
class TestCustomParser(CustomParserTestcase):
    broker_class = ConfluentKafkaBroker
