from faststream.nats import NatsBroker, TestNatsBroker
from tests.asgi.testcase import AsgiTestcase


class TestNatsAsgi(AsgiTestcase):
    def get_broker(self, **kwargs):
        return NatsBroker(**kwargs)

    def get_test_broker(self, broker):
        return TestNatsBroker(broker)
