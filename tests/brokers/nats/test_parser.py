import pytest

from faststream.nats import NatsBroker
from tests.brokers.base.parser import CustomParserTestcase


@pytest.mark.nats
class TestCustomParser(CustomParserTestcase):
    broker_class = NatsBroker
