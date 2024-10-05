from .base import BaseAsgiTestCase
from .test_rabbit import TestCaseRabbit


class TestCaseAsgiRabbit(BaseAsgiTestCase, TestCaseRabbit):
    doc_path = "docs.docs_src.getting_started.prometheus.rabbit_asgi"
