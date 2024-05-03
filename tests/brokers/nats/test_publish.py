import pytest

from faststream.nats import NatsBroker
from tests.brokers.base.publish import BrokerPublishTestcase


@pytest.mark.nats()
class TestPublish(BrokerPublishTestcase):
    """Test publish method of NATS broker."""

    @pytest.fixture()
    def pub_broker(self):
        return NatsBroker()
