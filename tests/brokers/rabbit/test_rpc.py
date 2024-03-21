import pytest

from tests.brokers.base.rpc import BrokerRPCTestcase, ReplyAndConsumeForbidden


@pytest.mark.rabbit()
class TestRPC(BrokerRPCTestcase, ReplyAndConsumeForbidden):  # noqa: D101
    pass
