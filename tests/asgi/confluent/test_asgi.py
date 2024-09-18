from faststream.confluent import KafkaBroker, TestKafkaBroker
from tests.asgi.testcase import AsgiTestcase


class TestConfluentAsgi(AsgiTestcase):
    def get_broker(self, **kwargs):
        return KafkaBroker(**kwargs)

    def get_test_broker(self, broker):
        return TestKafkaBroker(broker)
