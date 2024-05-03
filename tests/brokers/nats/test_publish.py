import pytest

from faststream.nats import NatsBroker
from tests.brokers.base.publish import BrokerPublishTestcase


@pytest.mark.nats()
class TestPublish(BrokerPublishTestcase):
    """Test publish method of NATS broker."""

    def get_broker(self) -> NatsBroker:
        return NatsBroker()
