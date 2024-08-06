from faststream.confluent import KafkaBroker, TestKafkaBroker
from tests.asgi.testcase import AsgiTestcase


class TestConfluentAsgi(AsgiTestcase):
    def get_broker(self):
        return KafkaBroker()

    def get_test_broker(self, broker):
        return TestKafkaBroker(broker)
