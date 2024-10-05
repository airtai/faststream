from .base import BaseAsgiTestCase
from .test_nats import TestCaseNats


class TestCaseAsgiNats(BaseAsgiTestCase, TestCaseNats):
    doc_path = "docs.docs_src.getting_started.prometheus.nats_asgi"
