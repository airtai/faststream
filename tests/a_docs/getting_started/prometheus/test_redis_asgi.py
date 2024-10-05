from .base import BaseAsgiTestCase
from .test_redis import TestCaseRedis


class TestCaseAsgiRedis(BaseAsgiTestCase, TestCaseRedis):
    doc_path = "docs.docs_src.getting_started.prometheus.redis_asgi"
