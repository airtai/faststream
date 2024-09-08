import pytest

from faststream.confluent import KafkaBroker
from tests.brokers.base.parser import CustomParserTestcase

from .basic import ConfluentTestcaseConfig


@pytest.mark.confluent
class TestCustomParser(ConfluentTestcaseConfig, CustomParserTestcase):
    broker_class = KafkaBroker
