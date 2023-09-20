import pytest

from tests.brokers.base.consume import BrokerRealConsumeTestcase


@pytest.mark.nats
class TestConsume(BrokerRealConsumeTestcase):
    pass
