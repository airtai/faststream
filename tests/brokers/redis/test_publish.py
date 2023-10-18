import pytest

from tests.brokers.base.publish import BrokerPublishTestcase


@pytest.mark.redis
class TestPublish(BrokerPublishTestcase):
    pass
