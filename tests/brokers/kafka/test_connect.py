import pytest

from faststream.kafka import KafkaBroker
from tests.brokers.base.connection import BrokerConnectionTestcase


@pytest.mark.kafka()
class TestConnection(BrokerConnectionTestcase):
    broker = KafkaBroker

    def get_broker_args(self, settings):
        return {"bootstrap_servers": settings.url}
