from faststream.redis import RedisBroker, TestRedisBroker
from tests.asgi.testcase import AsgiTestcase


class TestRedisAsgi(AsgiTestcase):
    def get_broker(self, **kwargs):
        return RedisBroker(**kwargs)

    def get_test_broker(self, broker):
        return TestRedisBroker(broker)
