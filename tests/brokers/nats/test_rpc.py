import pytest

from tests.brokers.base.rpc import BrokerRPCTestcase, ReplyAndConsumeForbidden


@pytest.mark.nats
class TestRPC(BrokerRPCTestcase, ReplyAndConsumeForbidden):
    pass
