from faststream.rabbit import RabbitBroker, TestRabbitBroker
from tests.asgi.testcase import AsgiTestcase


class TestRabbitAsgi(AsgiTestcase):
    def get_broker(self, **kwargs):
        return RabbitBroker(**kwargs)

    def get_test_broker(self, broker):
        return TestRabbitBroker(broker)
