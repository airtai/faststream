import pytest

from faststream.rabbit import RabbitBroker
from tests.brokers.base.rpc import BrokerRPCTestcase, ReplyAndConsumeForbidden


@pytest.mark.rabbit
class TestRPC(BrokerRPCTestcase, ReplyAndConsumeForbidden):
    def get_broker(self, apply_types: bool = False) -> RabbitBroker:
        return RabbitBroker(apply_types=apply_types)
