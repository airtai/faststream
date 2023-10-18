import pytest

from tests.brokers.base.consume import BrokerRealConsumeTestcase


@pytest.mark.redis
class TestConsume(BrokerRealConsumeTestcase):
    pass
