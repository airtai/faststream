from .base import BaseTestCase


class TestCaseRedis(BaseTestCase):
    middleware_cls_path = "faststream.redis.prometheus.RedisPrometheusMiddleware"
    broker_cls_path = "faststream.redis.RedisBroker"
    doc_path = "docs.docs_src.getting_started.prometheus.redis"
