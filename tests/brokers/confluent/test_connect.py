import pytest

from faststream.confluent import KafkaBroker
from tests.brokers.base.connection import BrokerConnectionTestcase


@pytest.mark.confluent
class TestConnection(BrokerConnectionTestcase):
    broker = KafkaBroker

    def get_broker_args(self, settings):
        return {"bootstrap_servers": settings.url}
