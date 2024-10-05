from .base import BaseAsgiTestCase
from .test_confluent import TestCaseConfluent


class TestCaseAsgiConfluent(BaseAsgiTestCase, TestCaseConfluent):
    doc_path = "docs.docs_src.getting_started.prometheus.confluent_asgi"
