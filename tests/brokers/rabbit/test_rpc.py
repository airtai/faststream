import pytest

from tests.brokers.base.rpc import BrokerRPCTestcase, ReplyAndConsumeForbidden


@pytest.mark.rabbit
class TestRPC(BrokerRPCTestcase, ReplyAndConsumeForbidden):
    pass
