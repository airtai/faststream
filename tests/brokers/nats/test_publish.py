import pytest

from tests.brokers.base.publish import BrokerPublishTestcase


@pytest.mark.nats()
class TestPublish(BrokerPublishTestcase):  # noqa: D101
    pass
