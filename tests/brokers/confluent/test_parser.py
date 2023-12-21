import pytest

from faststream.kafka import ConfluentKafkaBroker
from tests.brokers.base.parser import CustomParserTestcase


@pytest.mark.confluent()
class TestCustomParser(CustomParserTestcase):
    """A class to represent a test Kafka broker."""

    broker_class = ConfluentKafkaBroker
