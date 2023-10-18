import pytest

from tests.brokers.base.rpc import BrokerRPCTestcase, ReplyAndConsumeForbidden


@pytest.mark.redis
class TestRPC(BrokerRPCTestcase, ReplyAndConsumeForbidden):
    pass
